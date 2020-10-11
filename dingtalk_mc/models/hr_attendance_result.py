# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020 SuXueFeng GNU
###################################################################################
from odoo import models, fields, api, SUPERUSER_ID
import logging
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrAttendanceResult(models.Model):
    _name = "hr.attendance.result"
    _rec_name = 'employee_id'
    _description = "打卡结果"

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

    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id, index=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', index=True)
    work_date = fields.Date(string=u'工作日')
    record_id = fields.Char(string='唯一标识ID', help="钉钉设置的值为id，odoo中为record_id")
    check_type = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')], index=True)
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult, index=True)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    baseCheckTime = fields.Datetime(string=u'基准时间', help="计算迟到和早退，基准时间")
    check_in = fields.Datetime(string="实际打卡时间", required=True, help="实际打卡时间,  用户打卡时间的毫秒数")
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)
    work_month = fields.Char(string='年月字符串', help="为方便其他模块按照月份获取数据时使用", index=True)

    @api.model
    def create(self, values):
        """
        创建时触发
        :param values:
        :return:
        """
        if values['work_date']:
            values.update({'work_month': "{}/{}".format(values['work_date'][:4], values['work_date'][5:7])})
        return super(HrAttendanceResult, self).create(values)

    @api.model
    def process_dingtalk_chat(self, msg, company):
        """
        接受来自钉钉考勤回调的处理
        :param msg: 回调消息
        :param company: 公司
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                # 只处理员工打卡事件
                if msg.get('EventType') == 'attendance_check_record':
                    date_list = msg.get('DataList')
                    # 当员工发生打卡事件时，写入一条用户签到记录。
                    self.create_sign_rec(date_list, company)
                    # 执行拉取员工考勤记录信息

                else:
                    _logger.info("EventType: {}".format(msg.get('EventType')))

    def create_sign_rec(self, date_list, company):
        """
        创建签到记录
        :return:
        """
        for data in date_list:
            domain = [('ding_id', '=', data.get('userId')), ('company_id', '=', company.id)]
            employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain, limit=1)
            self.env['dingtalk.signs.list'].with_user(SUPERUSER_ID).create({
                'company_id': company.id,
                'emp_id': employee.id if employee else False,
                'checkin_time': dt.timestamp_to_local_date(data.get('checkTime'), self),
                'place': '',
                'visit_user': '',
                'detail_place': data.get('address'),
                'remark': "员工打卡",
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            })


class AttendanceMonthResult(models.Model):
    _name = 'hr.month.attendance'
    _description = "月考勤统计"
    _rec_name = 'employee_id'

    month_code = fields.Char(string="考勤年月", index=True, store=True, compute='_compute_month')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id, index=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', index=True)
    start_date = fields.Date(string="开始日期", default=fields.Date.context_today, required=True)
    end_date = fields.Date(string="结束日期", default=fields.Date.context_today)
    normal_count = fields.Float(string="正常打卡", digits=(16, 2))
    early_count = fields.Float(string="早退次数", digits=(16, 2))
    late_count = fields.Float(string="迟到次数", digits=(16, 2))
    absenteeism_count = fields.Float(string="旷工次数", digits=(16, 2))
    signed_count = fields.Float(string="未打卡次数", digits=(16, 2))
    overtime_days = fields.Float(string="加班天数", digits=(16, 1))
    travel_days = fields.Float(string="出差天数", digits=(16, 1))
    leave_days = fields.Float(string="请假天数", digits=(16, 1))

    @api.depends('start_date')
    def _compute_month(self):
        """
        :return:
        """
        for res in self:
            str_date = str(res.start_date)
            res.month_code = "{}/{}".format(str_date[:4], str_date[5:7])


# class HrAttendance(models.AbstractModel):
#     _inherit = "hr.attendance"
#
#     TimeResult = [
#         ('Normal', '正常'),
#         ('Early', '早退'),
#         ('Late', '迟到'),
#         ('SeriousLate', '严重迟到'),
#         ('Absenteeism', '旷工迟到'),
#         ('NotSigned', '未打卡'),
#     ]
#     SourceType = [
#         ('ATM', '考勤机'),
#         ('BEACON', 'IBeacon'),
#         ('DING_ATM', '钉钉考勤机'),
#         ('USER', '用户打卡'),
#         ('BOSS', '老板改签'),
#         ('APPROVE', '审批系统'),
#         ('SYSTEM', '考勤系统'),
#         ('AUTO_CHECK', '自动打卡')
#     ]
#
#     work_date = fields.Date(string=u'工作日')
#     work_month = fields.Char(string='年月字符串', help="为方便其他模块按照月份获取数据时使用", index=True)
#     source_type = fields.Selection(string=u'数据来源', selection=SourceType)
#     time_result = fields.Selection(string="打卡结果", selection=TimeResult)
#
#     @api.model
#     def create(self, vals):
#         """
#         创建时触发
#         :param vals:
#         :return:
#         """
#         if vals.get('work_date'):
#             vals.update({'work_month': "{}/{}".format(vals['work_date'][:4], vals['work_date'][5:7])})
#         return super(HrAttendance, self).create(vals)
#
#     @api.constrains('check_in', 'check_out', 'employee_id')
#     def _check_validity(self):
#         return
#
#     @api.constrains('check_in', 'check_out')
#     def _check_validity_check_in_check_out(self):
#         """ verifies if check_in is earlier than check_out. """
#         for attendance in self:
#             if attendance.check_in and attendance.check_out:
#                 if attendance.check_out < attendance.check_in:
#                     return
