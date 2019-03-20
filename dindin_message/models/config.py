# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

""" 工作消息 """


class MessageType(models.Model):
    _name = 'dindin.message.type'
    _description = "消息类型"
    _rec_name = 'name'

    name = fields.Char(string='类型名称')
    code = fields.Char(string='类型码')
    description = fields.Char(string='描述')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'请不要重复创建类型!'),
    ]
