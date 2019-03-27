import base64
import json
import logging
import time
import requests
from dingtalk.client.api.base import DingTalkBaseAPI

from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.http import request
from Crypto.Cipher import AES
from urllib.parse import quote
from . import aes_code
import hmac
from dingtalk.client.api.callback import Callback
_logger = logging.getLogger(__name__)


class CallBack(Home, http.Controller):

    @http.route('/callback/user_add_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        json_str = request.jsonrequest
        logging.info("json_str: {}".format(json_str))
        # json_str: {'encrypt': 'YshiTRKJARv6jnUU7y5SBu+FSZcL43yCiA/X28VGNYtHMHzSX5AdgfO17NlDjv8bUoQtfPOwhAuoZDLAwgYCdOPiIpJ8IIoQZwlACjhGewS/D90aNYZ9Np8eSGwkEMMp'}
        # signature: eeb3bcaa04345367459d146e9a50370d76494670
        # timestamp: 1553600935486
        # nonce: xcIRHz4s
        signature = request.httprequest.args['signature']
        logging.info("signature: {}".format(signature))
        timestamp = request.httprequest.args['timestamp']
        logging.info("timestamp: {}".format(timestamp))
        nonce = request.httprequest.args['nonce']
        logging.info("nonce: {}".format(nonce))
        dd = DingTalkBaseAPI()
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'register_call_back')]).value
        dd.API_BASE_URL = url
        res = Callback(dd).register_call_back(call_back_tags='user_add_org', token='123456', aes_key='4g5j64qlyl3zvetqxz5jiocdr586fn2zvjpa8zls3ij', url='http://mysxfblog.asuscomm.com:8070/callback/user_add_org')
        print(res)


    # AES解密
    def decrypt(self, encrypt, encrData):
        # encrData = base64.b64decode(encrData)
        # unpad = lambda s: s[0:-s[len(s)-1]]
        unpad = lambda s: s[0:-s[-1]]
        cipher = AES.new(encrypt, AES.MODE_ECB)
        decrData = unpad(cipher.decrypt(encrData))
        return decrData.decode('utf-8')

    # 解密后，去掉补足的'\0'用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, IV=self.key)
        plain_text = cryptor.decrypt(base64.b64decode(text))
        return plain_text.rstrip('\0')