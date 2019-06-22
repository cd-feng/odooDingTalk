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
            action = self.env.ref('dindin_attendance.dingding_attendance_action').read()[0]
            action['domain'] = [('emp_id', '=', res.id)]
            return action


class DingDingAttendance(models.Model):
    _name = "dingding.attendance"
    _rec_name = 'emp_id'
    _description = "钉钉出勤"

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
        ('AUTO_CHECK', '自动打卡'),
        ('odoo', 'Odoo系统'),
    ]
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    check_in = fields.Datetime(string="打卡时间", default=fields.Datetime.now, required=True)
    ding_group_id = fields.Many2one(comodel_name='dindin.simple.groups', string=u'钉钉考勤组')
    recordId = fields.Char(string='记录ID')
    workDate = fields.Datetime(string=u'工作日')
    checkType = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')])
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    baseCheckTime = fields.Datetime(string=u'基准时间')
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)
    attendance_id = fields.Char(string='钉钉id')


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
            emps = self.env['hr.employee'].search([('din_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_attendance_list(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        global has_more
        logging.info(">>>开始获取员工打卡信息...")
        for res in self:
            user_list = list()
            emp_len = len(res.emp_ids)
            if emp_len > 50:
                n = 1
                e_list = list()
                for emp in res.emp_ids:
                    if n <= 50:
                        e_list.append(emp.din_id)
                        n = n + 1
                    else:
                        user_list.append(e_list)
                        e_list = list()
                        e_list.append(emp.din_id)
                        n = 2
                user_list.append(e_list)
            else:
                for emp in res.emp_ids:
                    if not emp.din_id:
                        raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(emp.name))
                    user_list.append(emp.din_id)
            logging.info(user_list)
            for u in user_list:
                if isinstance(u, str):
                    offset = 0
                    limit = 50
                    while True:
                        work_data_from = datetime.strptime(str(res.start_date), "%Y-%m-%d %H:%M:%S")
                        work_data_to = datetime.strptime(str(res.stop_date), "%Y-%m-%d %H:%M:%S")
                        delta = timedelta(days=7)
                        if work_data_to < work_data_from  + delta:
                            work_data_to_mid = work_data_to
                        else:
                            work_data_to_mid = work_data_from + delta
                        while (work_data_from < work_data_to):
                            data = {
                                'workDateFrom': str(work_data_from),  
                                'workDateTo': str(work_data_to_mid),  
                                'userIdList': user_list,  
                                'offset': offset,
                                'limit': limit,
                            }
                            has_more = self.send_post_dindin(data)
                            work_data_from = work_data_to_mid + timedelta(days=1)
                            work_data_to_mid += delta

                        if not has_more:
                            break
                        else:
                            offset = offset + limit
                        break
                elif isinstance(u, list):
                    offset = 0
                    limit = 50
                    while True:
                        work_data_from = datetime.strptime(str(res.start_date), "%Y-%m-%d %H:%M:%S")
                        work_data_to = datetime.strptime(str(res.stop_date), "%Y-%m-%d %H:%M:%S")
                        delta = timedelta(days=7)
                        if work_data_to < work_data_from  + delta:
                            work_data_to_mid = work_data_to
                        else:
                            work_data_to_mid = work_data_from + delta
                        while (work_data_from < work_data_to):
                            data = {
                                'workDateFrom': str(work_data_from),  
                                'workDateTo': str(work_data_to_mid),  
                                'userIdList': u,  
                                'offset': offset,
                                'limit': limit,
                            }
                            has_more = self.send_post_dindin(data)
                            work_data_from = work_data_to_mid + timedelta(days=1)
                            work_data_to_mid += delta
                        if not has_more:
                            break
                        else:
                            offset = offset + limit
            logging.info(">>>根据日期获取员工打卡信息结束...")
        action = self.env.ref('dindin_attendance.dingding_attendance_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def send_post_dindin(self, data):
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'attendance_list')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=15)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                for rec in result.get('recordresult'):
                        data = {
                            'recordId': rec.get('recordId'),
                            'workDate': self.get_time_stamp(rec.get('workDate')),  # 工作日
                            'timeResult': rec.get('timeResult'),  # 时间结果
                            'locationResult': rec.get('locationResult'),  # 考勤结果
                            'baseCheckTime': self.get_time_stamp(rec.get('baseCheckTime')),  # 基准时间
                            'sourceType': rec.get('sourceType'),  # 数据来源
                            'checkType': rec.get('checkType'),
                            'check_in': self.get_time_stamp(rec.get('userCheckTime')),
                            'attendance_id': rec.get('id'),
                        }
                        groups = self.env['dindin.simple.groups'].sudo().search(
                            [('group_id', '=', rec.get('groupId'))])
                        data.update({'ding_group_id': groups[0].id if groups else False})
                        emp_id = self.env['hr.employee'].sudo().search([('din_id', '=', rec.get('userId'))])
                        data.update({'emp_id': emp_id[0].id if emp_id else False})
                        attendance = self.env['dingding.attendance'].sudo().search(
                            [('emp_id', '=', emp_id[0].id),
                             ('check_in', '=', self.get_time_stamp(rec.get('userCheckTime'))),
                             ('checkType', '=', rec.get('checkType'))])
                        if not attendance:
                            self.env['dingding.attendance'].sudo().create(data)
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