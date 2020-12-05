# -*- coding: utf-8 -*-

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class NewUserGroups(models.Model):
    _description = '新用户权限'
    _name = 'authing.user.groups'
    
    name = fields.Char(string="名称", required=True)
    groups_ids = fields.Many2many(comodel_name='res.groups', string=u'权限列表')

