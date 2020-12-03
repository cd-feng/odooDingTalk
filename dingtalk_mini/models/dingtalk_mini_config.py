# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class DingTalkMiniConfig(models.Model):
    _name = 'dingtalk.mini.config'
    _description = "钉钉小程序参数配置"
    _rec_name = 'name'

    company_id = fields.Many2one('res.company', string='关联公司', default=lambda self: self.env.user.company_id)
    name = fields.Char(string='小程序名称', index=True, required=True)
    agent_id = fields.Char(string=u'小程序AgentId')
    corp_id = fields.Char(string=u'CorpId')
    app_key = fields.Char(string=u'AppKey')
    app_secret = fields.Char(string=u'AppSecret')
    m_login = fields.Boolean(string="钉钉免登？", help="开启后允许从钉钉工作台免密码登录到odoo系统。")
    token = fields.Boolean(string="Token")

