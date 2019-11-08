# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
from odoo import models, fields, api


class HrLeavesList(models.Model):
    _name = "hr.leaves.list"
    _rec_name = 'user_id'
    _description = "请假列表"

    user_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    din_jobnumber = fields.Char(string='工号')
    duration_unit = fields.Selection(string=u'请假单位', selection=[('percent_day', '天'), ('percent_hour', '小时')])
    duration_percent = fields.Float(string=u'请假时长', digits=(10, 1))
    start_time = fields.Datetime(string=u'请假开始时间')
    end_time = fields.Datetime(string=u'请假结束时间')
    start_time_stamp = fields.Char(string='开始时间戳字符串')
    end_time_stamp = fields.Char(string='结束时间戳字符串')
