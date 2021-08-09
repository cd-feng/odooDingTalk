# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DingTalkCallbackLog(models.Model):
    _description = '回调日志'
    _name = 'dingtalk.callback.log'
    _rec_name = 'create_date'

    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.user.company_id)
    event_type = fields.Char(string="类型代码")
    body = fields.Text(string="消息内容")
    type_id = fields.Many2one(comodel_name="dingtalk.callback.list", string="回调类型")

    @api.model
    def create_dingtalk_log(self, company_id, encrypt_result, event_type):
        """
        创建钉钉回调日志
        :return:
        """
        type_id = self.env['dingtalk.callback.list'].sudo().search([('value', '=', event_type)], limit=1)
        return self.sudo().create({
            'company_id': company_id.id,
            'event_type': event_type,
            'body': encrypt_result,
            'type_id': type_id.id,
        })
