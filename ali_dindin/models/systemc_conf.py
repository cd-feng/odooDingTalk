# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DingDingPayConfig(models.Model):
    _description = '系统参数列表'
    _name = 'ali.dindin.system.conf'

    name = fields.Char(string='名称')
    key = fields.Char(string='key值')
    value = fields.Char(string='参数值')
    state = fields.Selection(string=u'有效', selection=[('y', '是'), ('n', '否'), ], default='y')

    _sql_constraints = [
        ('key_uniq', 'unique(key)', u'系统参数中key值不允许重复!'),
    ]
