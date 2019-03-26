# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DinDinCallbackList(models.Model):
    _name = 'dindin.users.callback.list'
    _description = "回调类型列表"
    _rec_name = 'name'

    ValueType = [
        ('00', '通讯录事件'),
        ('01', '群会话事件'),
        ('02', '签到事件'),
        ('03', '审批事件'),
    ]

    name = fields.Char(string='类型名')
    value = fields.Char(string='类型代码')
    value_type = fields.Selection(string=u'事件分类', selection=ValueType, default='')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)

    _sql_constraints = [
        ('value_uniq', 'unique(value)', u'类型代码重复!'),
        ('name_uniq', 'unique(name)', u'类型名重复!'),
    ]
