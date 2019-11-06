# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
import werkzeug
from werkzeug.exceptions import BadRequest
from odoo import SUPERUSER_ID, api, http, _
from odoo import registry as registry_get
from odoo.addons.auth_oauth.controllers.main import OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.auth_oauth.controllers.main import fragment_to_query_string
from odoo.addons.web.controllers.main import (login_and_redirect, ensure_db, set_cookie_and_redirect)
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class OAuthController(Controller):

    @http.route('/web/dingtalk/auto/login', type='http', auth='none')
    def web_dingtalk_auto_login(self, **kw):
        """
        免登入口
        :param kw:
        :return:
        """
        logging.info(">>>用户正在使用免登...")
        data = {'corp_id': dingtalk_api.get_dt_corp_id()}
        if request.session.uid:
            request.session.uid = False
        if request.session.login:
            request.session.login = False
        return request.render('dingtalk_login.auto_login_signup', data)

    @http.route('/web/dingtalk/auto/login/action', type='http', auth='none')
    @fragment_to_query_string
    def web_dingtalk_auto_signin_action(self, **kw):
        """
        通过获得的【免登授权码或者临时授权码】获取用户信息
        :param kw:
        :return:
        """
        auth_code = kw.get('authCode')
        logging.info(">>>免登授权码: %s", auth_code)
        result = dingtalk_api.get_client().user.getuserinfo(auth_code)
        employee = request.env['hr.employee'].sudo().search([('ding_id', '=', result.userid)], limit=1)
        if not employee:
            _logger.info(_("系统对应员工不存在!"))
            return self._do_err_redirect(_("系统对应员工不存在!"))
        _logger.info(">>>员工{}正在尝试登录系统".format(employee.name))
        if not employee.ding_id:
            _logger.info(_("员工不存在钉钉ID，请维护后再试!"))
            return self._do_err_redirect(_("员工不存在钉钉ID，请维护后再试!"))
        ensure_db()
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                credentials = env['res.users'].sudo().auth_oauth('dingtalk', employee.ding_id)
                cr.commit()
                url = '/web'
                resp = login_and_redirect(*credentials, redirect_url=url)
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                    resp.location = '/'
                return resp
            except AttributeError:
                _logger.error(">>>未在数据库'%s'上安装auth_signup：oauth注册已取消。" % (dbname,))
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                _logger.info('>>>DingTalk-OAuth2: 访问被拒绝，在存在有效会话的情况下重定向到主页，而未设置Cookie')
                url = "/web/login?oauth_error=3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
            except Exception as e:
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(url)

    def _do_err_redirect(self, errmsg):
        """
        返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        err_values = request.params.copy()
        err_values['error'] = _(errmsg)
        http.redirect_with_hash('/web/login')
        return request.render('dingtalk_login.result_signup', err_values)


class DingTalkLogin(Home, http.Controller):

    @http.route('/web/dingtalk/login', type='http', auth='public', website=True, sitemap=False)
    def web_dingtalk_login(self, *args, **kw):
        """
        主页点击钉钉扫码登录route 将返回到扫码页面
        :param args:
        :param kw:
        :return:
        """
        login_id = dingtalk_api.get_login_id()
        redirect_url = '{}web/dingtalk/login/action'.format(request.httprequest.host_url)
        url = "https://oapi.dingtalk.com/connect/qrconnect?appid={}&response_type=code&scope=snsapi_login&state=odoo&redirect_uri={}".format(login_id, redirect_url)
        return http.redirect_with_hash(url)

    @http.route('/web/dingtalk/account/login', type='http', auth='public', website=True, sitemap=False)
    def web_dingding_account_login(self, *args, **kw):
        """
        主页点击钉钉账号密码登录 重定向到钉钉登录页
        :param args:
        :param kw:
        :return:
        """
        login_id = dingtalk_api.get_login_id()
        redirect_url = '{}web/dingtalk/login/action'.format(request.httprequest.host_url)
        url = "https://oapi.dingtalk.com/connect/oauth2/sns_authorize?appid={}&response_type=code&scope=snsapi_login&state=odoo&redirect_uri={}".format(login_id, redirect_url)
        return http.redirect_with_hash(url)

    @http.route('/web/dingtalk/login/action', type='http', auth="none")
    @fragment_to_query_string
    def web_dingtalk_login_action(self, **kw):
        """
        接受到钉钉返回的数据时进入此方法
        1. 根据返回的临时授权码获取员工的信息
        2. 查找本地员工对应的关联系统用户。
        3. 界面跳转
        :param kw:
        :return:
        """
        code = request.params['code']
        _logger.info(">>>钉钉登录返回code参数为：{}".format(code))
        try:
            # 换取用户身份信息
            result = dingtalk_api.get_user_info_by_code(code)
            user_info = result.user_info
            _logger.info(">>>用户身份信息:{}".format(user_info))
            employee = request.env['hr.employee'].sudo().search([('din_unionid', '=', user_info.get('unionid'))], limit=1)
            if not employee:
                return self._do_error_redirect(_("{}在当前ERP系统中不存在".format(user_info.get('nick'))))
        except Exception as e:
            logging.info(e)
            return self._do_error_redirect(e)
        if not employee.user_id:
            return self._do_error_redirect(_("登录员工{}未关联系统用户，请维护后再试。 *_*!".format(employee.name)))
        return self._do_post_login(employee)

    def _do_post_login(self, employee):
        """
        :param employee:  employee
        :return:
        """
        ensure_db()
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                credentials = env['res.users'].sudo().auth_oauth('dingtalk', employee.ding_id)
                cr.commit()
                url = '/web'
                resp = login_and_redirect(*credentials, redirect_url=url)
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                    resp.location = '/'
                return resp
            except AttributeError:
                _logger.error(">>>未在数据库'%s'上安装auth_signup：oauth注册已取消。" % (dbname,))
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                _logger.info(
                    '>>>DingTalk-OAuth2: 访问被拒绝，在存在有效会话的情况下重定向到主页，而未设置Cookie')
                url = "/web/login?oauth_error=3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
            except Exception as e:
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(url)

    def _do_error_redirect(self, errmsg):
        """
        返回到主界面并返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        err_values = request.params.copy()
        err_values['error'] = _(errmsg)
        http.redirect_with_hash('/web/login')
        return request.render('dingtalk_login.result_signup', err_values)

