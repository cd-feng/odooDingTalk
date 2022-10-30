# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class Dingtalk2AttendanceList(models.Model):
    _name = "dingtalk2.attendance.list"
    _description = "考勤打卡结果"
    _order = 'user_check_time asc'

    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company, index=True)
    active = fields.Boolean(string="Active", default=True)
    name = fields.Many2one(comodel_name='hr.employee', string='员工', index=True, ondelete='cascade')
    department_id = fields.Many2one('hr.department', string='部门', related='name.department_id', store=True)

    source_type = fields.Selection(string='数据来源', selection=[
        ('ATM', '考勤机打卡'), ('BEACON', 'IBeacon'), ('DING_ATM', '钉钉考勤机'),
        ('USER', '用户打卡'), ('BOSS', '老板改签'),   ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'), ('AUTO_CHECK', '自动打卡')])
    base_check_time = fields.Datetime(string='基准时间', help="计算迟到和早退，基准时间")
    user_check_time = fields.Datetime(string="实际打卡时间", required=True)
    location_result = fields.Selection(string='位置结果', selection=[
        ('Normal', '范围内'), ('Outside', '范围外'), ('NotSigned', '未打卡')])
    time_result = fields.Selection(string='时间结果', selection=[
        ('Normal', '正常'), ('Early', '早退'), ('Late', '迟到'), ('SeriousLate', '严重迟到'),
        ('Absenteeism', '旷工迟到'), ('NotSigned', '未打卡')], index=True)
    check_type = fields.Selection(string='考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')], index=True)
    work_date = fields.Date(string='工作日')
    record_id = fields.Char(string='打卡记录ID')
    plan_id = fields.Char(string='排班ID')
    group_id = fields.Char(string='考勤组ID')
    ding_id = fields.Char(string='钉钉唯一标识ID')



