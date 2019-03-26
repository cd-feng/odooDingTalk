# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class InheritResUsers(models.Model):
    _inherit = ['res.users']

    @api.model
    def _get_defaultdin_pwd(self):
        return base64.b64encode('123456'.encode('utf-8'))

    din_password = fields.Char(string='钉钉登录密码', default=_get_defaultdin_pwd, size=64)

    def _set_password(self):
        for user in self:
            user.sudo().write({'din_password': base64.b64encode(user.password.encode('utf-8'))})
        super(InheritResUsers, self)._set_password()

