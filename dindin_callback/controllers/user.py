import logging
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
from odoo.http import request
from urllib.parse import quote
_logger = logging.getLogger(__name__)
import json
from .dingtalk_crypto import DingTalkCrypto


class CallBack(Home, http.Controller):

    @http.route('/callback/user_add_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        json_str = request.jsonrequest
        logging.info(">>>encrypt:{}".format(json_str.get('encrypt')))
        din_corpId = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
        encode_aes_key = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'encode_aes_key')]).value
        token = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'call_back_token')]).value
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
            encode_aes_key,
            token,
            din_corpId
        )
        randstr, length, msg, suite_key = crypto.decrypt(json_str.get('encrypt'))
        msg = json.loads(msg)
        logging.info(">>>解密后的消息结果:{}".format(msg))
        # 返回加密结果
        encrypt_msg = crypto.encrypt('success')
        encrypt_msg = encrypt_msg.decode()
        actual_sig, actual_time, actual_nonce = crypto.sign(encrypt_msg)
        logging.info("--------------------------------------------")
        logging.info("actual_sig：{}".format(actual_sig))
        logging.info("actual_time：{}".format(actual_time))
        logging.info("actual_nonce：{}".format(actual_nonce))
        logging.info("encrypt_msg：{}".format(encrypt_msg))
        logging.info("--------------------------------------------")
        return json.dumps({
                "msg_signature": actual_sig,
                "timeStamp": actual_time,
                "nonce": actual_nonce,
                "encrypt": encrypt_msg
            })


