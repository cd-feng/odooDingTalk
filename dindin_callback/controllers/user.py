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
        print(encrypt_msg)
        randstr, length, msg, suite_key = crypto.decrypt2(encrypt_msg)
        print(randstr)
        # print(length)
        # print(msg)
        # print(suite_key)

        return {
                "msg_signature": "111108bb8e6dbce3c9671d6fdb69d15066227608",
                "timeStamp": "1783610513",
                "nonce": "123456",
                "encrypt": quote("1ojQf0NSvw2WPvW7LijxS8UvISr8pdDP+rXpPbcLGOmIBNbWetRg7IP0vdhVgkVwSoZBJeQwY2zhROsJq/HJ+q6tp1qhl9L1+ccC9ZjKs1wV5bmA9NoAWQiZ+7MpzQVq+j74rJQljdVyBdI/dGOvsnBSCxCVW0ISWX0vn9lYTuuHSoaxwCGylH9xRhYHL9bRDskBc7bO0FseHQQasdfghjkl")
            }


