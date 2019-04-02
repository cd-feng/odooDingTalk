# -*- coding: utf-8 -*-
import json
import logging
import time
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class CallBack(Home, http.Controller):

    # 钉钉回调
    @http.route('/callback/eventreceive', type='json', auth='none', methods=['POST'], csrf=False)
    def callback_users(self, **kw):
        logging.info(">>>钉钉回调事件")
        json_str = request.jsonrequest
        call_back, din_corpId = self.get_bash_attr()
        msg = self.encrypt_result(json_str.get('encrypt'), call_back.aes_key, din_corpId)
        logging.info("-------------------------------------------")
        logging.info(">>>解密消息结果:{}".format(msg))
        logging.info("-------------------------------------------")
        msg = json.loads(msg)
        if msg.get('EventType') == 'user_add_org':
            logging.info(">>>钉钉回调-用户增加事件")
        # 返回加密结果
        return self.result_success(call_back.aes_key, call_back.token, din_corpId)

    def result_success(self, encode_aes_key, token, din_corpid):
        """
        封装success返回值
        :param encode_aes_key:
        :param token:
        :param din_corpid:
        :return:
        """
        from .dingtalk.crypto import DingTalkCrypto as dtc
        dc = dtc(encode_aes_key, din_corpid)
        # 加密数据
        encrypt = dc.encrypt('success')
        timestamp = str(int(round(time.time())))
        nonce = dc.generateRandomKey(8)
        # 生成签名
        signature = dc.generateSignature(nonce, timestamp, token, encrypt)
        new_data = {
            'json': True,
            'data': {
                'msg_signature': signature,
                'timeStamp': timestamp,
                'nonce': nonce,
                'encrypt': encrypt
            }
        }
        return new_data

    def encrypt_result(self, encrypt, encode_aes_key, din_corpid):
        """
        解密钉钉回调返回的值
        :param encrypt:
        :param encode_aes_key:
        :param din_corpid:
        :return: json-string
        """
        from .dingtalk.crypto import DingTalkCrypto as dtc
        dc = dtc(encode_aes_key, din_corpid)
        return dc.decrypt(encrypt)

    def get_bash_attr(self):
        """
        :return:
        """
        call_back = request.env['dindin.users.callback'].sudo().search([])
        if not call_back:
            raise UserError("钉钉回调管理单据错误，无法获取token和encode_aes_key值!")
        din_corpId = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
        if not din_corpId:
            raise UserError("钉钉CorpId值为空，请前往设置中进行配置!")
        return call_back[0], din_corpId
