import json
import logging
import time
import requests
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.http import request
from urllib.parse import quote
import hmac

_logger = logging.getLogger(__name__)


class CallBack(Home, http.Controller):

    @http.route('/callback/user_add_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        json_str = request.jsonrequest
        logging.info("json_str: {}".format(json_str))
        # {'encrypt': 'IdnYCATXhvxz3wIWAs+McsrPK2NmXMFr4oLlurOZqC5QOCA6EMepVy1T62ZDDIKsdr4ZSSysbb19ESvT40q+X9ClN+Oyu/OWHiKcglpLzH4QIIX04TASucp+eiFOyJvA'}
        # signature: 2ca973d785c9a3498b412bcc85130aa115914ff1
        # timestamp: 1553587396502
        # nonce: NT8O0b4o
        signature = request.httprequest.args['signature']
        logging.info("signature: {}".format(signature))
        timestamp = request.httprequest.args['timestamp']
        logging.info("timestamp: {}".format(timestamp))
        nonce = request.httprequest.args['nonce']
        logging.info("nonce: {}".format(nonce))
        return json.dumps({
  "msg_signature":"111108bb8e6dbce3c9671d6fdb69d15066227608",
  "timeStamp":"1783610513",
  "nonce":"123456",
  "encrypt":"1ojQf0NSvw2WPvW7LijxS8UvISr8pdDP+rXpPbcLGOmIBNbWetRg7IP0vdhVgkVwSoZBJeQwY2zhROsJq/HJ+q6tp1qhl9L1+ccC9ZjKs1wV5bmA9NoAWQiZ+7MpzQVq+j74rJQljdVyBdI/dGOvsnBSCxCVW0ISWX0vn9lYTuuHSoaxwCGylH9xRhYHL9bRDskBc7bO0FseHQQasdfghjkl"
  }, ensure_ascii=False)

