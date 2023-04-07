# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DingTalk2Config(models.Model):
    _inherit = 'dingtalk2.config'

    is_open_login = fields.Boolean(string="开启钉钉登录", default=False)
    oauth_id = fields.Many2one(comodel_name="auth.oauth.provider", string="oauth服务商")

    @api.constrains('app_key', 'is_open_login')
    def _constraint_app_key(self):
        """
        动态调整钉钉登录项（oauth）
        """
        for res in self:
            oauth_id = self.env.ref('dingtalk2_login.dingtalk2_login_auth_oauth').sudo()
            oauth_id.write({
                'client_id': res.app_key,
                'enabled': True if res.is_open_login else False,
            })

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
