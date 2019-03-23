# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import logging
import time
import urllib
import requests
from requests import ReadTimeout
from odoo import http, _
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.http import request
from urllib.parse import quote
import hmac

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
        code = request.params['code']
        if not code:
            logging.info("错误的访问地址,请输入正确的访问地址")
        logging.info(">>>获取的code为：{}".format(code))
        userid = False
        # ------------------------
        #   获取用户信息
        # ------------------------
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'getuserinfo_bycode')]).value
        login_appid = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appid')
        key = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appsecret')
        current_milli_time = lambda: int(round(time.time() * 1000))
        msg = str(current_milli_time())
        # ------------------------
        #   最坑的地方--签名
        # ------------------------
        signature = hmac.new(key.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).digest()
        signature = quote(base64.b64encode(signature), 'utf-8')
        data = {
            'tmp_auth_code': code
        }
        headers = {'Content-Type': 'application/json'}
        new_url = "{}signature={}&timestamp={}&accessKey={}".format(url, signature, msg, login_appid)
        try:
            result = requests.post(url=new_url, headers=headers, data=json.dumps(data), timeout=15)
            result = json.loads(result.text)
            logging.info(">>>扫码登录获取用户信息返回结果{}".format(result))
            if result.get('errcode') == 0:
                user_info = result.get('user_info')
                userid = self.getUseridByUnionid(user_info.get('unionid'))
            else:
                logging.info('>>>扫码登录获取用户信息失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            logging.info("网络连接超时！")
        print(userid)
        return json.dumps({"state": 'OK了'}, ensure_ascii=False)

    def getUseridByUnionid(self, unionid):
        """根据unionid获取userid"""
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'getUseridByUnionid')]).value
        token = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'token')]).value
        data = {'unionid': unionid}
        result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
        logging.info(">>>根据unionid获取userid获取结果:{}".format(result.text))
        result = json.loads(result.text)
        if result.get('errcode') == 0:
            return result.get('userid')
        else:
            logging.info(">>>根据unionid获取userid获取结果失败，原因为:{}".format(result.get('errmsg')))
