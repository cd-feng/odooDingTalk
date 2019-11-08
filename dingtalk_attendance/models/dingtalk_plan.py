# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrDingTalkPlan(models.Model):
    _name = "hr.dingtalk.plan"
    _rec_name = 'plan_id'
    _description = "排班列表"

    plan_id = fields.Char(string='钉钉排班ID')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])
    approve_id = fields.Char(string='审批id', help="没有的话表示没有审批单")
    user_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    class_id = fields.Char(string='考勤班次id')
    class_setting_id = fields.Char(string='班次配置id', help="没有的话表示使用全局班次配置")
    plan_check_time = fields.Datetime(string=u'打卡时间', help="数据库中存储为不含时区的时间UTC=0")
    group_id = fields.Many2one(comodel_name='dingtalk.simple.groups', string=u'考勤组')


