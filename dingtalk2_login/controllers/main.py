# -*- coding: utf-8 -*-
import json
import logging
import time
import werkzeug
from werkzeug.exceptions import BadRequest
from odoo import SUPERUSER_ID, api, http, exceptions
from odoo.addons.auth_oauth.controllers.main import OAuthLogin, OAuthController, fragment_to_query_string
from odoo import registry as registry_get
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
import hmac
import hashlib
import base64
from urllib.parse import quote
_logger = logging.getLogger(__name__)


class DingTalk2Login(OAuthLogin):

    def list_providers(self):
        """
        拓展登录页面的登录选项，针对钉钉登录单独封装登录参数，使用原生的好像不行。扫码后无法跳转回来
        """
        providers = super(DingTalk2Login, self).list_providers()
        for provider in providers:
            if provider['name'] == 'DingTalk Login':
                return_url = request.httprequest.url_root + 'auth_oauth/signin'
                state = self.get_state(provider)
                state['app_key'] = provider['client_id']
                params = dict(
                    redirect_uri=return_url,
                    response_type='code',
                    appid=provider['client_id'],
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers


class Dingtalk2OAuthController(OAuthController):

    def get_dingtalk_user_data_by_code(self, code, dingtalk_config):
        """
        根据code获取用户信息
        :param code:
        :param dingtalk_config:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(request, dingtalk_config.company_id))
        timestamp = str(int(round(time.time() * 1000)))
        signature = hmac.new(dingtalk_config.app_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
        signature = quote(base64.b64encode(signature), 'utf-8')
        url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(
            signature, timestamp, dingtalk_config.app_key)
        result = client.post(url, {
            'tmp_auth_code': code,
        })
        return result.user_info

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        """
        这里直接重写的auth_oauth/signin函数，用于支持钉钉回调并进行登录
        """
        state = json.loads(kw['state'])
        dbname = state['d']
        if not http.db_filter([dbname]):
            return BadRequest()
        provider = state['p']
        context = state.get('c', {})
        app_key = state.get('app_key', False)      # 钉钉AppKey
        auth_code = kw.get('code', False)          # 授权码
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                if app_key and auth_code:         # 针对钉钉登录的特殊处理
                    _logger.info("钉钉授权码: {}, 钉钉AppKey：{}".format(auth_code, app_key))
                    dingtalk_config = env['dingtalk2.config'].search([('app_key', '=', app_key)], limit=1)
                    if not dingtalk_config:
                        _logger.info("未找到对应钉钉组织:{}".format(app_key))
                    user_info = self.get_dingtalk_user_data_by_code(auth_code, dingtalk_config)
                    _logger.info(">>>用户身份信息:{}".format(user_info))
                    unionid = user_info.get('unionid')
                    db, login, key = env['res.users'].sudo().auth_oauth('dingtalk2_login', unionid)
                else:
                    db, login, key = env['res.users'].sudo().auth_oauth(provider, kw)
                cr.commit()
                action = state.get('a')
                menu = state.get('m')
                redirect = werkzeug.urls.url_unquote_plus(state['r']) if state.get('r') else False
                url = '/web'
                if redirect:
                    url = redirect
                elif action:
                    url = '/web#action=%s' % action
                elif menu:
                    url = '/web#menu_id=%s' % menu
                pre_uid = request.session.authenticate(db, login, key)
                resp = request.redirect(_get_login_redirect_url(pre_uid, url), 303)
                resp.autocorrect_location_header = False
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user._is_internal():
                    resp.location = '/'
                return resp
            except AttributeError:   # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled." % (dbname,))
                url = "/web/login?oauth_error=1"
            except AccessDenied:     # oauth credentials not valid, user could be on a temporary session
                _logger.info('OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
                url = "/web/login?oauth_error=3"
                redirect = request.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
            except Exception as e:     # signup error
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"
        redirect = request.redirect(url, 303)
        redirect.autocorrect_location_header = False
        return redirect


