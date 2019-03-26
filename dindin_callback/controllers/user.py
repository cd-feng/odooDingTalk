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
    def callback_user_add_org(self, redirect=None, **kw):
        json_str = request.jsonrequest
        logging.info("json_str: {}".format(json_str))
        signature = request.params['signature']
        logging.info("signature: {}".format(signature))
        timestamp = request.params['timestamp']
        logging.info("timestamp: {}".format(timestamp))
        nonce = request.params['nonce']
        logging.info("nonce: {}".format(nonce))
        data = request.params.data
        logging.info("data: {}".format(data))

