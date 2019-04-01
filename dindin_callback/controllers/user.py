import logging
import time
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
import json
from odoo.http import request
from .dingtalk_crypto import DingTalkCrypto

_logger = logging.getLogger(__name__)


class CallBack(Home, http.Controller):

    @http.route('/callback/user_add_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        json_str = request.jsonrequest
        logging.info(">>>encrypt:{}".format(json_str.get('encrypt')))
        call_back_list = request.env['dindin.users.callback.list'].sudo().search([('value', '=', 'user_add_org')])
        call_back = request.env['dindin.users.callback'].sudo().search([('call_id', '=', call_back_list[0].id)])
        if not call_back:
            raise UserError("钉钉回调管理单据错误，无法获取token和encode_aes_key值!")
        din_corpId = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
        if not din_corpId:
            raise UserError("钉钉CorpId值为空，请前往设置中进行配置!")
        signature = request.httprequest.args['signature']
        logging.info(">>>signature: {}".format(signature))
        timestamp = request.httprequest.args['timestamp']
        logging.info(">>>timestamp: {}".format(timestamp))
        nonce = request.httprequest.args['nonce']
        logging.info(">>>nonce: {}".format(nonce))
        # 解密
        crypto = DingTalkCrypto(
            call_back[0].aes_key,
            call_back[0].token,
            din_corpId
        )
        randstr, length, msg, suite_key = crypto.decrypt(json_str.get('encrypt'))
        msg = json.loads(msg)
        logging.info(">>>解密后的消息结果:{}".format(msg))
        # 返回加密结果
        return self.result(call_back[0].aes_key, call_back[0].token, din_corpId)

    def result(self, encode_aes_key, token, din_corpId):
        """
        封装返回值
        :param encode_aes_key:
        :param token:
        :param din_corpId:
        :return:
        """
        from .dingtalk.crypto import DingTalkCrypto as dtc
        dingtalkCrypto = dtc(encode_aes_key, din_corpId)
        # 加密数据
        encrypt = dingtalkCrypto.encrypt('success')
        timestamp = str(int(round(time.time() * 1000)))
        nonce = dingtalkCrypto.generateRandomKey(8)
        # 生成签名
        signature = dingtalkCrypto.generateSignature(nonce, timestamp, token, encrypt)
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
