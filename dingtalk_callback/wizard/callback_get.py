# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class GetCallbackList(models.TransientModel):
    _name = 'get.dingtalk.callback'
    _description = "获取回调列表"
    _rec_name = 'id'

    def get_callback_list(self):
        self.ensure_one()
        try:
            result = dingtalk_api.get_client().callback.get_call_back()
            _logger.info(result)
            if result.get('errcode') != 0:
                raise UserError(result.get('errmsg'))
            tag_list = list()
            for tag in result.get('call_back_tag'):
                callback_list = self.env['dingtalk.callback.list'].search([('value', '=', tag)])
                if callback_list:
                    tag_list.append(callback_list[0].id)
            callbacks = self.env['dingtalk.callback.manage'].search([('url', '=', result.get('url'))])
            data = {
                'call_ids': [(6, 0, tag_list)],
                'url': result.get('url'),
                'aes_key': result.get('aes_key'),
                'token': result.get('token'),
                'state': '01',
            }
            if callbacks:
                callbacks.write(data)
            else:
                self.env['dingtalk.callback.manage'].create(data)
        except Exception as e:
            raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}
