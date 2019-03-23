# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, _
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.http import request

_logger = logging.getLogger(__name__)


class DinDinLogin(Home, http.Controller):

    @http.route('/web/dindin_login', type='http', auth='public', website=True, sitemap=False)
    def web_dindin_login(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        response = request.render('dindin_login.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/dindin_login/get_url', type='http', auth="none")
    def get_url(self, **kw):
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'sns_authorize')]).value
        login_appid = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appid')
        # 获取传递过来当前的url和端口信息
        local_url = request.params['local_url']
        redirect_url = "{}/web/action_login".format(local_url)
        new_url = "{}appid={}&response_type=code&scope=snsapi_login&redirect_uri={}".format(url, login_appid,
                                                                                            redirect_url)
        data = json.dumps({"encode_url": new_url, 'callback_url': redirect_url})
        return data

    @http.route('/web/action_login', type='http', auth="none")
    def action_ding_login(self, redirect=None, **kw):
        tmpcode = request.params['code']
        if not tmpcode:
            logging.info("错误的访问地址,请输入正确的访问地址")
        logging.info(">>>获取的code为：{}".format(tmpcode))
        return json.dumps({"state": 'OK了'}, ensure_ascii=False)
