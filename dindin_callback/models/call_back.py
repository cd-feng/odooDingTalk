# -*- coding: utf-8 -*-
import datetime
import json
import logging
import random
import string
import time
from urllib.parse import quote

import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
import json
from .dingtalk_crypto import DingTalkCrypto


class DinDinCallback(models.Model):
    _name = 'dindin.users.callback'
    _inherit = ['mail.thread']
    _description = "钉钉回调管理"
    _rec_name = 'call_id'

    @api.model
    def _get_default_aes_key(self):
        encode_aes_key = self.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'encode_aes_key')]).value
        return encode_aes_key

    @api.model
    def _get_default_token(self):
        token = self.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'call_back_token')]).value
        return token

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    call_id = fields.Many2one(comodel_name='dindin.users.callback.list', string=u'回调类型', ondelete='cascade')
    token = fields.Char(string='Token', default=_get_default_token, size=50)
    aes_key = fields.Char(string='数据加密密钥', default=_get_default_aes_key, size=50)
    url = fields.Char(string='回调URL', size=200)
    state = fields.Selection(string=u'状态', selection=[('00', '未注册'), ('01', '已注册')], default='00')
    
    _sql_constraints = [
        ('vcall_id_uniq', 'unique(call_id)', u'回调类型重复!'),
    ]

    @api.multi
    def register_call_back(self):
        """
        注册事件
        :return:
        """
        logging.info(">>>注册事件...")
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'register_call_back')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            call_list = list()
            call_list.append(res.call_id.value)
            data = {
                'call_back_tag': call_list if call_list else '',
                'token': res.token if res.token else '',
                'aes_key': res.aes_key if res.aes_key else '',
                'url': res.url if res.url else '',
            }
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    self.write({'state': '01'})
                else:
                    raise UserError("注册失败！原因:{}".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        logging.info(">>>注册事件End...")


