# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class Dingtalk2AttendanceSigns(models.Model):
    _name = 'dingtalk2.attendance.signs'
    _description = "签到记录"

    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company, index=True)
    name = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, ondelete='cascade')
    department_id = fields.Many2one('hr.department', string=u'部门', related='name.department_id', store=True)
    checkin_time = fields.Datetime(string=u'签到时间')
    detail_place = fields.Char(string='详细地址')
    remark = fields.Char(string='签到备注')
    place = fields.Char(string='签到地址')
    visit_user = fields.Char(string='拜访对象')



