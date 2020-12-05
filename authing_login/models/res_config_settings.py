# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020 SuXueFeng GNU
###################################################################################

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    authing_app_id = fields.Char(string="App ID", config_parameter='authing_login.default_authing_app_id')
    authing_client_id = fields.Char(string="用户池ID", config_parameter='authing_login.default_authing_client_id')
    authing_secret = fields.Char(string="应用秘钥", config_parameter='authing_login.default_authing_secret')
    authing_is_open = fields.Boolean(string="是否启用", config_parameter='authing_login.default_authing_is_open')
    authing_group_id = fields.Many2one("authing.user.groups", string="新用户权限", config_parameter='authing_login.default_authing_group_id')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        provider = self.env['auth.oauth.provider'].sudo().search([('name', '=', 'Authing')])
        if self.authing_is_open:
            if provider:
                provider.sudo().write({'client_id': self.authing_app_id, 'enabled': True})
            else:
                self.env['auth.oauth.provider'].sudo().create({
                    'name': 'Authing',
                    'client_id': self.authing_app_id,
                    'body': 'Authing登录',
                    'auth_endpoint': 'https://sso.authing.cn/authorize/',
                    'scope': 'user',
                    'validation_endpoint': 'https://sso.authing.cn/authenticate/',
                    'data_endpoint': 'https://users.authing.cn/oauth/user/userinfo/',
                    'css_class': 'fa fa-retweet',
                    'enabled': True,
                })
        else:
            if provider:
                provider.sudo().write({'enabled': False})



