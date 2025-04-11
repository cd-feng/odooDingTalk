# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions


class DingtalkSetting(models.Model):
    _name = 'dingtalk.setting'
    _description = '钉钉应用配置'

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string="公司", required=True, default=lambda self: self.env.company)
    name = fields.Char(string="企业名称", required=True)
    corp_id = fields.Char(string="企业CorpID", required=True)
    agent_id = fields.Char(string="Agent Id", required=True)
    app_key = fields.Char(string="App Key", required=True)
    app_secret = fields.Char(string="App Secret", required=True)

    is_create_dingtalk_user = fields.Boolean(string="是否创建用户")
    dingtalk_default_passwd = fields.Char(string="默认登录密码")
    is_get_emp_avatar = fields.Boolean(string="是否使用钉钉头像")
    description = fields.Text(string="备注")

    def get_setting_param(self, company_id):
        """
        获取配置参数实例
        """
        return self.search([('company_id', '=', company_id)], limit=1)
