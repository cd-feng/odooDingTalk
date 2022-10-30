# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DingTalk2Config(models.Model):
    _inherit = 'dingtalk2.config'

    is_open_login = fields.Boolean(string="开启钉钉登录", default=False)
    oauth_id = fields.Many2one(comodel_name="auth.oauth.provider", string="oauth服务商")

    @api.onchange('is_open_login')
    def _onchange_open_dingtalk_login(self):
        """
        状态发生变化时，动态调整钉钉登录项（oauth）
        """
        # TODO 需要改成新版的链接 https://open.dingtalk.com/document/orgapp-server/tutorial-obtaining-user-personal-information
        oauth_obj = self.env['auth.oauth.provider'].sudo()
        body = '钉钉登录[%s]' % self.name
        value = {
            'name': 'DingTalk Login',
            'client_id': self.app_key,
            'auth_endpoint': 'https://oapi.dingtalk.com/connect/qrconnect',
            'scope': 'snsapi_login',
            'validation_endpoint': 'null',
            'css_class': 'fa fa-fw fa-connectdevelop',
            'body': body,
            'enabled': True if self.is_open_login else False,
        }
        oauth_id = oauth_obj.search([('body', '=', body)], limit=1)
        if oauth_id:
            oauth_id.write(value)
        else:
            oauth_id = oauth_obj.create(value)
        self.oauth_id = oauth_id.id

    def sync_employee_login_information(self):
        """
        将当前公司内的员工登录用到的ding_unionid写入到user中
        """
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id), ('ding_unionid', '!=', False), ('user_id', '!=', False)]
        for emp in self.env['hr.employee'].sudo().search(domain):
            emp.user_id.sudo().write({
                'oauth_uid': emp.ding_unionid,
                'oauth_provider_id': self.oauth_id.id,
            })
