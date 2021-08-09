# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class DingTalkCallbackList(models.Model):
    _name = 'dingtalk.callback.list'
    _description = "回调类型列表"
    _rec_name = 'name'

    ValueType = [
        ('00', '通讯录事件'),
        ('01', '群会话事件'),
        ('02', '签到事件'),
        ('03', '审批事件'),
        ('04', '考勤事件'),
    ]

    name = fields.Char(string='类型名')
    value = fields.Char(string='类型代码')
    call_back_url = fields.Char(string='回调地址函数')
    color = fields.Integer(string=u'color')
    value_type = fields.Selection(string=u'事件分类', selection=ValueType)

    _sql_constraints = [
        ('value_uniq', 'unique(value)', u'类型代码重复!'),
        ('name_uniq', 'unique(name)', u'类型名重复!'),
    ]
