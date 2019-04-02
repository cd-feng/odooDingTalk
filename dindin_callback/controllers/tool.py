# -*- coding: utf-8 -*-
import time
from odoo.exceptions import UserError
from odoo.http import request


def result_success(encode_aes_key, token, din_corpid):
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


def encrypt_result(encrypt, encode_aes_key, din_corpid):
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


def get_bash_attr(value_type):
    """
    :param value_type:
    :return:
    """
    call_back = request.env['dindin.users.callback'].sudo().search([('value_type', '=', value_type)])
    if not call_back:
        raise UserError("钉钉回调管理单据错误，无法获取token和encode_aes_key值!")
    din_corpId = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
    if not din_corpId:
        raise UserError("钉钉CorpId值为空，请前往设置中进行配置!")
    return call_back, din_corpId
