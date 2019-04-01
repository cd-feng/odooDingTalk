# -*- coding: utf-8 -*-
import json
import logging
import time

import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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

    @api.onchange('call_id')
    def onchage_call_type(self):
        if self.call_id:
            self.url = self.call_id.call_back_url

    @api.multi
    def register_call_back(self):
        """
        注册事件
        :return:
        """
        logging.info(">>>注册事件...")
        # self.test_encode()
        # return False
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
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    self.write({'state': '01'})
                else:
                    raise UserError("注册失败！原因:{}".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        logging.info(">>>注册事件End...")

    # def test_encode(self):
    #     """
    #     测试加密数据
    #     :return:
    #     """
    #     from .dingtalk_crypto import DingTalkCrypto
    #     # 解密
    #     din_corpId = 'suite4xxxxxxxxxxxxxxx'
    #     encode_aes_key = '4g5j64qlyl3zvetqxz5jiocdr586fn2zvjpa8zls3ij'
    #     token = '123456'
    #
    #     encrypt = '1a3NBxmCFwkCJvfoQ7WhJHB+iX3qHPsc9JbaDznE1i03peOk1LaOQoRz3+nlyGNhwmwJ3vDMG+OzrHMeiZI7gTRWVdUBmfxjZ8Ej23JVYa9VrYeJ5as7XM/ZpulX8NEQis44w53h1qAgnC3PRzM7Zc/D6Ibr0rgUathB6zRHP8PYrfgnNOS9PhSBdHlegK+AGGanfwjXuQ9+0pZcy0w9lQ=='
    #     crypto = DingTalkCrypto(
    #         encode_aes_key,
    #         token,
    #         din_corpId
    #     )
    #     randstr, length, msg, suite_key = crypto.decrypt(encrypt)
    #     msg = json.loads(msg)
    #     logging.info(">>>解密后的消息结果:{}".format(msg))
    #
    #     from .dingtalk.main import DingTalk
    #     from .dingtalk.crypto import DingTalkCrypto
    #     dingtalkCrypto = DingTalkCrypto(encode_aes_key, din_corpId)
    #     # 加密数据
    #     encrypt = dingtalkCrypto.encrypt('success')
    #     # 获取当前时间戳
    #     timestamp = str(int(round(time.time() * 1000)))
    #     # 获取随机字符串
    #     nonce = dingtalkCrypto.generateRandomKey(8)
    #     # 生成签名
    #     signature = dingtalkCrypto.generateSignature(nonce, timestamp, token, encrypt)
    #     result = {
    #         'json': True,
    #         'data': {
    #             'msg_signature': signature,
    #             'timeStamp': timestamp,
    #             'nonce': nonce,
    #             'encrypt': encrypt
    #         }
    #     }
    #     print(result)
