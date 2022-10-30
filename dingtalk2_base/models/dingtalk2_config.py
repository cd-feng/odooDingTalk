# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from odoo.addons.dingtalk2_base.tools.dingtalk2_tools import get_random_character


class DingTalk2Config(models.Model):
    _name = 'dingtalk2.config'
    _description = "钉钉参数配置"
    _rec_name = 'name'

    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.company)
    name = fields.Char(string='钉钉企业名称', required=True)
    corp_id = fields.Char(string='CorpId', required=True)
    agent_id = fields.Char(string='AgentId', required=True)
    app_key = fields.Char(string='AppKey', required=True)
    app_secret = fields.Char(string='AppSecret', required=True)
    encrypt_aes_key = fields.Char(string="订阅加密AesKey", default=get_random_character(size=43))
    encrypt_token = fields.Char(string="订阅签名Token", default=get_random_character(size=25))

    @api.constrains('company_id')
    def _constraint_company_id(self):
        """
        每个公司只能对应一个参数配置
        """
        for res in self:
            if self.search_count([('company_id', '=', res.company_id.id)]) > 1:
                raise exceptions.ValidationError("请注意：每个公司只能配置一个钉钉参数.")

