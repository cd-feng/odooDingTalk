# -*- coding: utf-8 -*-
import base64
import functools
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import quote

import requests
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest

from odoo import SUPERUSER_ID, api, http
from odoo import registry as registry_get
from odoo.addons.auth_oauth.controllers.main import \
    OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import (login_and_redirect,
                                              set_cookie_and_redirect)
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request
from odoo.tools import pycompat

_logger = logging.getLogger(__name__)


def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        kw.pop('debug', False)
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)
    return wrapper


class OAuthLogin(Home):
    def list_providers(self):
        """
        oauth2登录入口
        :param kw:
        :return:
        """
        result = super(OAuthLogin, self).list_providers()
        for provider in result:
            if 'dingtalk' in provider['auth_endpoint']:
                return_url = request.httprequest.url_root + 'dingding/auto/login'
                state = self.get_state(provider)
                params = dict(
                    response_type='code',
                    appid=provider['client_id'],  # appid 是钉钉移动应用的appId
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))

        return result


class OAuthController(Controller):
    @http.route('/dingding/auto/login/in', type='http', auth='none')
    def dingding_auto_login(self, **kw):
        """
        免登入口
        :param kw:
        :return:
        """
        logging.info(">>>用户正在使用免登...")
        data = {'corp_id': request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')}
        return request.render('dindin_login.dingding_auto_login', data)

    @http.route('/dingding/auto/login', type='http', auth='none')
    @fragment_to_query_string
    def auto_signin(self, **kw):
        """
        通过获得的【免登授权码或者临时授权码】获取用户信息
        :param kw:
        :return:
        """
        if kw.get('authcode'):  # 免登
            auth_code = kw.get('authcode')
            _logger.info("获得的auth_code: %s", auth_code)
            userid = self.get_userid_by_auth_code(auth_code).get('userid')
            state = dict(
                d=request.session.db,
                p='dingtalk',
            )

        elif kw.get('code'):  # 扫码或密码登录
            tmp_auth_code = kw.get('code', "")
            _logger.info("获得的tmp_auth_code: %s", tmp_auth_code)
            unionid = self.get_unionid_by_tmp_auth_code(tmp_auth_code)
            userid = self.get_userid_by_unionid(unionid)
            state = json.loads(kw['state'])

        mobile = self.get_user_mobile_by_userid(userid)
        dbname = state['d']
        if not http.db_filter([dbname]):
            return BadRequest()
        provider = 'dingtalk'
        # provider = state['p']
        context = state.get('c', {})
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth_dingtalk(provider, mobile)
                cr.commit()
                action = state.get('a')
                menu = state.get('m')
                redirect = werkzeug.url_unquote_plus(state['r']) if state.get('r') else False
                url = '/web'
                if redirect:
                    url = redirect
                elif action:
                    url = '/web#action=%s' % action
                elif menu:
                    url = '/web#menu_id=%s' % menu
                resp = login_and_redirect(*credentials, redirect_url=url)
                # Since /web is hardcoded, verify user has right to land on it
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                    resp.location = '/'
                return resp
            except AttributeError:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled." % (dbname,))
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                # oauth credentials not valid, user could be on a temporary session
                _logger.info(
                    'OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
                url = "/web/login?oauth_error=3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
            except Exception as e:
                # signup error
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"

        return set_cookie_and_redirect(url)

    def get_unionid_by_tmp_auth_code(self, tmp_auth_code):
        """
        根据返回的临时授权码获取用户信息
        :param tmp_auth_code:用户授权的临时授权码code，只能使用一次
        :return:
        """
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'getuserinfo_bycode')]).value
        login_appid = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appid')
        key = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appsecret')
        msg = pycompat.to_text(int(time.time() * 1000))
        # ------------------------
        # 签名
        # ------------------------
        signature = hmac.new(key.encode('utf-8'), msg.encode('utf-8'),
                             hashlib.sha256).digest()
        signature = quote(base64.b64encode(signature), 'utf-8')
        data = {
            'tmp_auth_code': tmp_auth_code
        }
        headers = {'Content-Type': 'application/json'}
        new_url = "{}signature={}&timestamp={}&accessKey={}".format(url, signature, msg, login_appid)
        try:
            result = requests.post(url=new_url, headers=headers, data=json.dumps(data), timeout=15)
            result = json.loads(result.text)
            logging.info(">>>钉钉登录获取用户信息返回结果{}".format(result))
            if result.get('errcode') == 0:
                user_info = result.get('user_info')
                return user_info['unionid']
            raise BadRequest(result)
        except Exception as e:
            return {'state': False, 'msg': "异常信息:{}".format(str(e))}

    def get_userid_by_unionid(self, unionid):
        """
        根据unionid获取userid
        """
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'getUseridByUnionid')]).value
        token = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'token')]).value
        data = {'unionid': unionid}
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
            logging.info(">>>根据unionid获取userid获取结果:{}".format(result.text))
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                return result.get('userid')
            raise BadRequest(result)
        except Exception as e:
            return {'state': False, 'msg': "异常信息:{}".format(str(e))}

    def get_userid_by_auth_code(self, auth_code):
        """
        根据返回的免登授权码获取用户userid
        :param auth_code:
        :return:
        """
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'get_userid')]).value
        token = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'token')]).value
        url = "{}?access_token={}&code={}".format(url, token, auth_code)
        try:
            result = requests.get(url=url, timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                return result.get('userid')
            raise BadRequest(result)
        except Exception as e:
            return {'state': False, 'msg': "异常信息:{}".format(str(e))}

    def get_user_mobile_by_userid(self, userid):
        """
        根据钉钉userid获取用户手机号
        :param userid:
        :return:
        """
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'user_get')]).value
        token = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'token')]).value
        data = {'userid': userid}
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                return result.get('mobile')
            raise BadRequest(result)
        except Exception as e:
            return {'state': False, 'msg': "异常信息:{}".format(str(e))}
