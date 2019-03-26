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

        signature = request.httprequest.args['signature']
        logging.info("signature: {}".format(signature))
        timestamp = request.httprequest.args['timestamp']
        logging.info("timestamp: {}".format(timestamp))
        nonce = request.httprequest.args['nonce']
        logging.info("nonce: {}".format(nonce))

