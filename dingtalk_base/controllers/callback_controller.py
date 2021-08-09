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
        callbacks = request.env['dingtalk.callback.manage'].sudo().search([])
        encrypt_result = False  # 解密后类型
        corp_id = False  # 钉钉企业的corp_id
        callback = False  # callback
        company_id = False  # 正在回调的公司
        for call in callbacks:
            # 遍历所有配置了多公司参数的公司配置
            config = request.env['dingtalk.config'].sudo().search([('company_id', '=', call.company_id.id)], limit=1)
            if not config:
                continue
            try:
                # 因无法确定是哪一个企业发起的回调。所以在此将每个企业的id用于解密，解密无异常就表示该企业发生了回调操作并记录下改企业对象
                dc = DingTalkCrypto(call.aes_key, config.corp_id)
                encrypt_result = dc.decrypt(json_str.get('encrypt'))
                callback = call
                corp_id = config.corp_id
                company_id = call.company_id
                break
            except Exception:
                continue
        if not encrypt_result or not corp_id or not callback:
            return False
        # 直接开线程进行处理
        processing = request.env['dingtalk.processing.callbacks']
        t = threading.Thread(target=processing.process_dingtalk_chat, args=(encrypt_result, company_id.id))
        t.start()
        # -----返回success说明已收到回调-----
        return self.result_dingtalk_callback_success(callback.aes_key, callback.token, corp_id)

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
        return return_data
