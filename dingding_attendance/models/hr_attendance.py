# -*- coding: utf-8 -*-
import json
import logging
import time
import requests
from requests import ReadTimeout
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    def dingding_attendance_action_employee(self):
        for res in self:
            action = self.env.ref('dingding_attendance.hr_attendance_result_action').read()[0]
            action['domain'] = [('emp_id', '=', res.id)]
            return action


class HrAttendanceResult(models.Model):
    _name = "hr.attendance.result"
    _rec_name = 'emp_id'
    _description = "员工打卡结果列表"

    TimeResult = [
        ('Normal', '正常'),
        ('Early', '早退'),
        ('Late', '迟到'),
        ('SeriousLate', '严重迟到'),
        ('Absenteeism', '旷工迟到'),
        ('NotSigned', '未打卡'),
    ]
    LocationResult = [
        ('Normal', '范围内'), ('Outside', '范围外'), ('NotSigned', '未打卡'),
    ]
    SourceType = [
        ('ATM', '考勤机'),
        ('BEACON', 'IBeacon'),
        ('DING_ATM', '钉钉考勤机'),
        ('USER', '用户打卡'),
        ('BOSS', '老板改签'),
        ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'),
        ('AUTO_CHECK', '自动打卡')
    ]
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    ding_group_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'钉钉考勤组')
    plan_id = fields.Many2one(comodel_name='hr.dingding.plan', string=u'排班')
    record_id = fields.Char(string='唯一标识ID', help="钉钉设置的值为id，odoo中为record_id")
    work_date = fields.Datetime(string=u'工作日')
    check_type = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')])
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    approveId = fields.Char(string='关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    procInstId = fields.Char(string='审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    baseCheckTime = fields.Datetime(string=u'基准时间', help="计算迟到和早退，基准时间")
    check_in = fields.Datetime(string="实际打卡时间", required=True, help="实际打卡时间,  用户打卡时间的毫秒数")
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult)
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)


class HrAttendanceTransient(models.TransientModel):
    _name = 'hr.attendance.tran'
    _description = '获取钉钉考勤信息'

    start_date = fields.Datetime(string=u'开始时间', required=True)
    stop_date = fields.Datetime(string=u'结束时间', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_dingding_attendance_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_attendance_list(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，
        钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        logging.info(">>>开始获取员工打卡信息...")
        user_list = list()
        for emp in self.emp_ids:
            if not emp.ding_id:
                raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(emp.name))
            user_list.append(emp.ding_id)
        user_list = self.list_cut(user_list, 50)
        for u in user_list:
            logging.info(">>>开始获取{}员工段数据".format(u))
            date_list = self.day_cut(self.start_date, self.stop_date, 7)
            for d in date_list:
                logging.info(">>>开始获取{}时间段数据".format(d))
                offset = 0
                limit = 50
                while True:
                    data = {
                        'workDateFrom': d[0],  
                        'workDateTo': d[1],  
                        'userIdList': u,
                        'offset': offset,
                        'limit': limit,
                    }
                    has_more = self.send_post_dindin(data)
                    logging.info(">>>是否还有剩余数据：{}".format(has_more))
                    if not has_more:
                        break
                    else:
                        offset = offset + limit
                        logging.info(">>>准备获取剩余数据中的第{}至{}条".format(offset+1, offset+limit))
        logging.info(">>>根据日期获取员工打卡信息结束...")
        action = self.env.ref('dingding_attendance.hr_attendance_result_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def send_post_dindin(self, data):
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('attendance_list')
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                for rec in result.get('recordresult'):
                    data = {
                        'record_id': rec.get('id'),
                        'work_date': self.get_time_stamp(rec.get('workDate')),  # 工作日
                        'timeResult': rec.get('timeResult'),  # 时间结果
                        'locationResult': rec.get('locationResult'),  # 考勤结果
                        'baseCheckTime': self.get_time_stamp(rec.get('baseCheckTime')),  # 基准时间
                        'sourceType': rec.get('sourceType'),  # 数据来源
                        'check_type': rec.get('checkType'),
                        'check_in': self.get_time_stamp(rec.get('userCheckTime')),
                        'approveId': rec.get('approveId'),
                    }
                    # 考勤组
                    groups = self.env['dingding.simple.groups'].sudo().search(
                        [('group_id', '=', rec.get('groupId'))], limit=1)
                    data.update({'ding_group_id': groups[0].id if groups else False})
                    # 员工
                    emp_id = self.env['hr.employee'].sudo().search([('ding_id', '=', rec.get('userId'))], limit=1)
                    data.update({'emp_id': emp_id[0].id if emp_id else False})
                    # 班次
                    plan = self.env['hr.dingding.plan'].sudo().search([('plan_id', '=', rec.get('planId'))], limit=1)
                    data.update({'plan_id': plan[0].id if plan else False})
                    # attendance = self.env['hr.attendance.result'].sudo().search(
                    #     [('emp_id', '=', emp_id[0].id),
                    #      ('check_in', '=', self.get_time_stamp(rec.get('userCheckTime'))),
                    #      ('check_type', '=', rec.get('checkType'))])
                    attendance = self.env['hr.attendance.result'].sudo().search([('record_id', '=', rec.get('id'))])
                    if not attendance:
                        self.env['hr.attendance.result'].sudo().create(data)
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")

    @api.model
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间
        :param timeNum:
        :return:
        """
        timeStamp = float(timeNum / 1000)
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime

    @api.model
    def list_cut(self, mylist, limit):
        """
        列表分段
        :param mylist:列表集
        :param limit: 子列表元素限制数量
        :return:
        """
        length = len(mylist)
        cut_list = [mylist[i:i+limit] for i in range(0, length, limit)]
        return cut_list
    
    @api.model
    def day_cut(self, begin_time, end_time, days):
        """
        日期分段
        :param begin_date:开始日期
        :param end_date:结束日期
        :param days: 最大间隔时间
        :return:
        """
        cut_day = []
        begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(str(end_time), "%Y-%m-%d %H:%M:%S")
        delta = timedelta(days=days)
        t1 = begin_time
        while t1 <= end_time:
            if end_time < t1 + delta:
                t2 = end_time
            else:
                t2 = t1 + delta
            t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
            t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
            cut_day.append([t1_str, t2_str])
            t1 = t2 + timedelta(seconds=1)
        return cut_day