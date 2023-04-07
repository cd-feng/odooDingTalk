# -*- coding: utf-8 -*-
import json
import logging
import requests
import werkzeug
from werkzeug.exceptions import BadRequest
from odoo import SUPERUSER_ID, api, http
from odoo.addons.auth_oauth.controllers.main import OAuthLogin, OAuthController, fragment_to_query_string
from odoo import registry as registry_get
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class DingTalk2Login(OAuthLogin):

    def list_providers(self):
        """
        拓展登录页面的登录选项，针对钉钉登录单独封装登录参数，使用原生的好像不行。扫码后无法跳转回来
        """
        providers = super(DingTalk2Login, self).list_providers()
        for provider in providers:
            if provider['name'] == 'DingTalk Login':
                redirect_uri = request.httprequest.url_root + 'auth_oauth/signin'
                db_name = self.get_state(provider)['d']
                state = "{},{}".format(db_name, provider['client_id'])   # state参数钉钉会返回
                auth_link = "{}?redirect_uri={}&response_type=code&client_id={}&scope=openid&state={}&prompt=consent".format(
                    provider['auth_endpoint'], redirect_uri, provider['client_id'], state
                )
                provider['auth_link'] = auth_link
        return providers


class Dingtalk2OAuthController(OAuthController):

    def get_dingtalk_user_data_by_code(self, auth_code, dingtalk_config):
        """
        根据code获取用户信息
        :param auth_code:
        :param dingtalk_config:
        :return:
        """
        user_token = self.get_dingtalk_user_token(dingtalk_config, auth_code)
        if not user_token:
            return {}
        _logger.info("获取的用户token为：%s" % user_token)
        # 获取用户通讯录个人信息
        try:
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "x-acs-dingtalk-access-token": user_token
            }
            result = requests.get(url='https://api.dingtalk.com/v1.0/contact/users/me',
                                  params=json.dumps({}), headers=headers, timeout=5)
            result = json.loads(result.text)
        except Exception as e:
            _logger.info("获取用户token失败： {}".format(str(e)))
            return {}
        return result

    @staticmethod
    def get_dingtalk_user_token(dingtalk_config, auth_code):
        """
        获取用户token
        """
        data = {
            "clientId": dingtalk_config.app_key,
            "clientSecret": dingtalk_config.app_secret,
            "code": auth_code,
            "grantType": "authorization_code"
        }
        try:
            result = requests.post(
                url='https://api.dingtalk.com/v1.0/oauth2/userAccessToken', data=json.dumps(data),
                headers={"Content-Type": "application/json; charset=UTF-8"}, timeout=3)
            result = json.loads(result.text)
        except Exception as e:
            _logger.info("获取用户token失败： {}".format(str(e)))
            return False
        return result.get('accessToken', False)

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        """
        这里直接重写的auth_oauth/signin函数，用于支持钉钉回调并进行登录
        """
        state = kw.get('state').split(',')
        dbname = state[0]      # 数据库名称
        app_key = state[1]     # 钉钉AppKey
        if not http.db_filter([dbname]):
            return BadRequest()
        auth_code = kw.get('authCode', False)          # 授权码
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                if app_key and auth_code:         # 针对钉钉登录的特殊处理
                    _logger.info("钉钉授权码: {}, 钉钉AppKey：{}".format(auth_code, app_key))
                    dingtalk_config = env['dingtalk2.config'].search([('app_key', '=', app_key)], limit=1)
                    if not dingtalk_config:
                        _logger.info("未找到对应钉钉组织:{}".format(app_key))
                    user_info = self.get_dingtalk_user_data_by_code(auth_code, dingtalk_config)
                    _logger.info(">>>用户身份信息:{}".format(user_info))
                    db, login, key = env['res.users'].sudo().auth_oauth('dingtalk2_login', user_info.get('unionId'))
                else:
                    db, login, key = env['res.users'].sudo().auth_oauth('dingtalk2_login', kw)
                cr.commit()
                pre_uid = request.session.authenticate(db, login, key)
                resp = request.redirect(_get_login_redirect_url(pre_uid, '/web'), 303)
                resp.autocorrect_location_header = False
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user._is_internal():
                    resp.location = '/'
                return resp
            except AttributeError:
                _logger.error("数据库 %s 上未安装auth_signup：oauth注册已取消。" % (dbname,))
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                _logger.info('OAuth2: 访问被拒绝，如果存在有效会话，则重定向到主页，而不设置cookie')
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

    @http.route('/dingtalk/signin', type='http', auth='none', website=True, sitemap=False)
    @fragment_to_query_string
    def dingtalk_signin(self, **kw):
        """
        钉钉应用内登录入口
        """
        logging.info(">>>用户正在使用免登...")
        if request.session.uid:
            return request.redirect('/web')
        return request.render('dingtalk2_login.dingtalk_signin', {'corp_id': kw.get('corpId')})

    @http.route('/dingtalk/signin/action', type='http', auth='none', website=True, sitemap=False)
    def dingtalk_signin_action(self, **kw):
        """
        通过获得的【免登授权码或者临时授权码】获取用户信息
        :param kw:
        :return:
        """
        auth_code, corp_id = kw.get('authCode'), kw.get('corpId')
        logging.info(">>>免登授权码: %s", auth_code)
        logging.info(">>>corp_id: %s", corp_id)
        config = request.env['dingtalk2.config'].sudo().search([('corp_id', '=', corp_id)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk2_config(request, config.company_id))
        try:
            result = client.user.getuserinfo(auth_code)
        except Exception as e:
            return str(e)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            return "员工[{}]未关联系统登录用户，请联系管理员处理！".format(employee.name)
        _logger.info(">>>员工：{}正在尝试钉钉免密系统".format(employee.name))
        if not employee.ding_id:
            return "员工[{}]不存在钉钉ID，请维护后再试!".format(employee.name)
        if not employee.user_id:
            return "没有关联系统用户，请联系管理员处理！"
        ensure_db()
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                db, login, key = env['res.users'].sudo().auth_oauth('dingtalk2_login', employee.ding_unionid)
                cr.commit()
                pre_uid = request.session.authenticate(db, login, key)
                resp = request.redirect(_get_login_redirect_url(pre_uid, '/web'), 303)
                resp.autocorrect_location_header = False
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user._is_internal():
                    resp.location = '/'
                return resp
            except Exception as e:
                return "登录时发生错误：{}".format(str(e))
