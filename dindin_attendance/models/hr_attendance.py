# -*- coding: utf-8 -*-
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Attendance"

    check_in = fields.Datetime(string="打卡时间", default=fields.Datetime.now, required=False)
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
    ding_group_id = fields.Many2one(comodel_name='dindin.simple.groups', string=u'钉钉考勤组')
    recordId = fields.Char(string='记录ID')
    workDate = fields.Date(string=u'工作日')
    checkType = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')])
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    baseCheckTime = fields.Datetime(string=u'基准时间')
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """
        取消系统自带验证出勤记录的有效性的验证
        :return:
        """
        return True


class HrAttendanceTransient(models.TransientModel):
    _name = 'hr.attendance.tran'
    _description = '获取钉钉考勤信息'

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_dingding_attendance_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('din_id', '!=', '')])
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
                        data = {
                            'workDateFrom': "{} 00:00:00".format(res.start_date),  # 开始日期
                            'workDateTo': "{} 00:00:00".format(res.stop_date),  # 结束日期
                            'userIdList': user_list,  # 员工列表
                            'offset': offset,  # 开始日期
                            'limit': limit,  # 开始日期
                        }
                        has_more = self.send_post_dindin(data)
                        if not has_more:
                            break
                        else:
                            offset = offset + limit
                    break
                elif isinstance(u, list):
                    offset = 0
                    limit = 50
                    while True:
                        data = {
                            'workDateFrom': "{} 00:00:00".format(res.start_date),  # 开始日期
                            'workDateTo': "{} 00:00:00".format(res.stop_date),  # 结束日期
                            'userIdList': u,  # 员工列表
                            'offset': offset,  # 开始日期
                            'limit': limit,  # 开始日期
                        }
                        has_more = self.send_post_dindin(data)
                        if not has_more:
                            break
                        else:
                            offset = offset + limit
            logging.info(">>>根据日期获取员工打卡信息结束...")
        action = self.env.ref('hr_attendance.hr_attendance_action')
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
            logging.info(result)
            if result.get('errcode') == 0:
                OnDuty_list = list()
                OffDuty_list = list()
                for rec in result.get('recordresult'):
                    baseCheckTime = self.get_time_stamp(rec.get('baseCheckTime'))
                    data = {
                        'recordId': rec.get('recordId'),
                        'workDate': self.get_time_stamp(rec.get('workDate')),  # 工作日
                        'timeResult': rec.get('timeResult'),  # 时间结果
                        'locationResult': rec.get('locationResult'),  # 考勤类型
                        'baseCheckTime': baseCheckTime,  # 基准时间
                        'sourceType': rec.get('sourceType'),  # 数据来源
                        'check_in': self.get_time_stamp(rec.get('userCheckTime'))
                    }
                    groups = self.env['dindin.simple.groups'].sudo().search([('group_id', '=', rec.get('groupId'))])
                    data.update({'ding_group_id': groups[0].id if groups else False})
                    emp_id = self.env['hr.employee'].sudo().search([('din_id', '=', rec.get('userId'))])
                    data.update({'employee_id': emp_id[0].id if emp_id else False})
                    if rec.get('checkType') == 'OnDuty':
                        data.update({'check_in': self.get_time_stamp(rec.get('userCheckTime'))})
                        OnDuty_list.append(data)
                    else:
                        data.update({'check_out': self.get_time_stamp(rec.get('userCheckTime'))})
                        OffDuty_list.append(data)
                for onduy in OnDuty_list:
                    attendance = self.env['hr.attendance'].sudo().search(
                        [('employee_id', '=', onduy.get('employee_id')),
                         ('baseCheckTime', '=', onduy.get('baseCheckTime'))])
                    if not attendance:
                        self.env['hr.attendance'].sudo().create(OnDuty_list)
                for off in OffDuty_list:
                    attendance = self.env['hr.attendance'].sudo().search([('employee_id', '=', off.get('employee_id')),
                                                                          ('baseCheckTime', '=',
                                                                           off.get('baseCheckTime'))])
                    for attend in attendance:
                        if not attend.check_out:
                            attend.write({'check_out': off.get('check_out')})
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