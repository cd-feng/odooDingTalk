# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class GetCallbackList(models.TransientModel):
    _name = 'get.dingtalk.callback'
    _description = "获取回调列表"
    _rec_name = 'id'

    company_ids = fields.Many2many('res.company', 'dingtalk_get_callback_rel', string="获取的公司", required=True,
                                   default=lambda self: [(6, 0, [self.env.company.id])])

    def get_callback_list(self):
        for company in self.company_ids:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            try:
                result = client.callback.get_call_back()
                _logger.info(result)
                tag_list = list()
                for tag in result.get('call_back_tag'):
                    callback_list = self.env['dingtalk.callback.list'].search([('value', '=', tag)])
                    if callback_list:
                        tag_list.append(callback_list[0].id)
                domain = [('url', '=', result.get('url')), ('company_id', '=', company.id)]
                callbacks = self.env['dingtalk.callback.manage'].search(domain)
                data = {
                    'call_ids': [(6, 0, tag_list)],
                    'url': result.get('url'),
                    'aes_key': result.get('aes_key'),
                    'token': result.get('token'),
                    'state': '01',
                    'company_id': company.id,
                }
                if callbacks:
                    callbacks.write(data)
                else:
                    self.env['dingtalk.callback.manage'].create(data)
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}
