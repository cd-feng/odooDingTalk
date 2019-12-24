# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dt_agent_id = fields.Char(string=u'AgentId')
    dt_corp_id = fields.Char(string=u'CorpId')
    dt_app_key = fields.Char(string=u'AppKey')
    dt_app_secret = fields.Char(string=u'AppSecret')
    dt_login_id = fields.Char(string=u'用于登录AppId')
    dt_login_secret = fields.Char(string=u'用于登录AppSecret')
    dt_token = fields.Boolean(string="自动获取应用Token")
    dt_delete_is_sy = fields.Boolean(string=u'删除基础数据自动同步?')
    dt_serial_number = fields.Char(string='授权许可号')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            dt_agent_id=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_agent_id') or '000',
            dt_corp_id=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id') or '000',
            dt_app_key=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_key') or '000',
            dt_app_secret=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_secret') or '000',
            dt_login_id=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id') or '000',
            dt_login_secret=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_secret') or '000',
            dt_token=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_token') or '000',
            dt_serial_number=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_serial_number'),
            dt_delete_is_sy=self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_delete_is_sy') or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_agent_id', self.dt_agent_id)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_corp_id', self.dt_corp_id)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_app_key', self.dt_app_key)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_app_secret', self.dt_app_secret)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_login_id', self.dt_login_id)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_login_secret', self.dt_login_secret)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_token', self.dt_token)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_serial_number', self.dt_serial_number)
        self.env['ir.config_parameter'].sudo().set_param('dingtalk_base.dt_delete_is_sy', self.dt_delete_is_sy)

