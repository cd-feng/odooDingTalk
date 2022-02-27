# -*- coding: utf-8 -*-

import threading
import time
from odoo import api, SUPERUSER_ID
from odoo.http import Controller, route, json, request
from .crypto import DingTalkCrypto
import logging
_logger = logging.getLogger(__name__)


class DingTalkCallBackManage(Controller):

    @route('/web/dingtalk/callback/action', type='json', auth='public', methods=['POST'], csrf=False)
    def web_dingtalk_callback_action(self, **kw):
        """
        回调函数入口-当收到钉钉的回调请求时，需要解密内容，然后根据回调类型做不同的处理
        :param kw:
        :return:
        """
        json_str = request.jsonrequest
        encrypt_result = False  # 解密后消息
        config = False      # config
        company_id = False  # 正在回调的公司
        for config in request.env['dingtalk.config'].with_user(SUPERUSER_ID).search([]):
            try:
                dc = DingTalkCrypto(config.encrypt_aes_key, config.encrypt_token)
                encrypt_result = dc.decrypt(json_str.get('encrypt'))
                config = config
                company_id = config.company_id
                break
            except:
                continue
        if not encrypt_result or not config:
            return False
        # 直接开线程进行处理
        processing = request.env['dingtalk.processing.callbacks']
        t = threading.Thread(target=processing.process_dingtalk_chat, args=(encrypt_result, company_id.id))
        t.start()
        # -----返回success说明已收到回调-----
        return self.result_dingtalk_callback_success(config.encrypt_aes_key, config.encrypt_token, config.app_key)

    def result_dingtalk_callback_success(self, encode_aes_key, token, corp_id):
        """
        封装success返回值
        :param encode_aes_key:
        :param token:
        :param corp_id:
        :return:
        """
        dc = DingTalkCrypto(encode_aes_key, corp_id)
        # 加密数据
        encrypt = dc.encrypt('success')
        timestamp = str(int(round(time.time())))
        nonce = dc.generateRandomKey(8)
        # 生成签名
        signature = dc.generateSignature(nonce, timestamp, token, encrypt)
        return_data = {
            'json': True,
            'data': {
                'msg_signature': signature,
                'timeStamp': timestamp,
                'nonce': nonce,
                'encrypt': encrypt
            }
        }
        _logger.info(return_data)
        return return_data
