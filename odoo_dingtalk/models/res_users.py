# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    dingtalk_user_id = fields.Char(string='钉钉用户Id', index=True)

