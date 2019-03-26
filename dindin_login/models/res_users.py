# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class InheritResUsers(models.Model):
    _inherit = ['res.users']

    din_password = fields.Char(string='钉钉登录密码', size=64)

    def _set_password(self):
        for user in self:
            user.sudo().write({'din_password': base64.b64encode(user.password.encode('utf-8'))})
        super(InheritResUsers, self)._set_password()
