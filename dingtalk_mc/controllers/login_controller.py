# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from werkzeug.exceptions import BadRequest
from odoo import SUPERUSER_ID, api, http, _
from odoo import registry as registry_get
from odoo.addons.auth_oauth.controllers.main import OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import fragment_to_query_string
from odoo.addons.web.controllers.main import (login_and_redirect, ensure_db, set_cookie_and_redirect)
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingTalkMcLogin(Controller):

    @http.route('/web/dingtalk/mc/login', type='http', auth='public', website=True, sitemap=False)
    def web_dingtalk_mc_login(self, *args, **kw):
        """
        主页点击钉钉扫码登录route 将返回到扫码页面
        :param args:
        :param kw:
        :return:
        """
        ensure_db()
        if not request.session.uid:
            return request.render('dingtalk_mc.dingtalk_mc_login_signup')
        request.uid = request.session.uid
        try:
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render('web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            if request.session.uid:
                request.session.uid = False
            if request.session.login:
                request.session.login = False
            return request.render('dingtalk_mc.dingtalk_mc_login_signup')

    @http.route('/web/dingtalk/mc/get/companys', type='http', auth='public', website=True, sitemap=False)
    def dingtalk_mc_get_companys(self):
        result = {
            "company_list": request.env['res.company'].sudo().search_read([], ['name', 'id'])
        }
        return json.dumps(result)

    @http.route('/web/dingtalk/mc/get_url', type='http', auth="none")
    def dingtalk_mc_get_url(self, **kw):
        """
        拼接访问钉钉的验证用户的url
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        local_url = params_data.get('local_url')
        company_id = int(params_data.get('company_id'))
        config = request.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company_id)], limit=1)
        if not config:
            return json.dumps({'state': False, 'error': '该公司未设置扫码登录'})
        redirect_url = "{}/web/dingtalk/mc/login/action".format(local_url)
        url = "https://oapi.dingtalk.com/connect/oauth2/sns_authorize?appid={}&response_type=code&scope=" \
              "snsapi_login&redirect_uri={}&state={}".format(config.login_id, redirect_url, company_id)
        data = json.dumps({"encode_url": url, 'callback_url': redirect_url})
        return data

    @http.route('/web/dingtalk/mc/login/action', type='http', auth="none", website=True, sitemap=False)
    @fragment_to_query_string
    def dingtalk_mc_login_action(self, **kw):
        """
        接受到钉钉返回的数据
        1. 根据返回的临时授权码获取员工的信息
        2. 查找本地员工对应的关联系统用户。
        3. 界面跳转
        :param kw:
        :return:
        """
        # 接受返回的数据
        params_data = request.params.copy()
        code = params_data.get('code')
        company_id = params_data.get('state')
        company = request.env['res.company'].sudo().search([('id', '=', int(company_id))], limit=1)
        _logger.info(">>>钉钉登录返回code参数为：{}".format(code))
        try:
            user_info = dt.user_info_by_dingtalk_code(request, code, company)
            _logger.info(">>>用户身份信息:{}".format(user_info))
            domain = [('din_unionid', '=', user_info.get('unionid')), ('company_id', '=', int(company_id))]
            employee = request.env['hr.employee'].sudo().search(domain, limit=1)
            if not employee:
                return self.do_error_redirect(_("钉钉用户: '{name}' 在当前系统中不存在,或许管理员暂未添加登陆账号。".format(name=user_info.get('nick'))))
        except Exception as e:
            return self.do_error_redirect(str(e))
        if not employee.user_id:
            return self.do_error_redirect(_("员工:'{name}' 未关联系统用户，请联系管理员处理。".format(name=employee.name)))
        return self.user_login_by_emp(employee)

    def user_login_by_emp(self, employee):
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
                err_str = "OAuth2: %s" % str(e)
                _logger.exception(err_str)
                return self.do_error_redirect(err_str)
        return http.redirect_with_hash(url)

    def do_error_redirect(self, errmsg):
        """
        返回到主界面并返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        ding_error = request.params.copy()
        ding_error.update({
            'ding_error': errmsg,
        })
        _logger.info("扫码登陆失败,Error:{}".format(ding_error))
        response = request.render('dingtalk_mc.dingtalk_mc_login_result_signup', ding_error)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class OAuthController(Controller):

    @http.route('/web/dingtalk/mc/auto/login', type='http', auth='public', website=True)
    def web_dingtalk_mc_auto_login(self, **kw):
        """
        免登入口
        :param kw:
        :return:
        """
        ensure_db()
        logging.info(">>>用户正在使用免登...")
        if request.session.uid:
            request.uid = request.session.uid
            try:
                context = request.env['ir.http'].webclient_rendering_context()
                response = request.render('web.webclient_bootstrap', qcontext=context)
                response.headers['X-Frame-Options'] = 'DENY'
                return response
            except AccessError as e:
                _logger.info("AccessError: {}".format(str(e)))
        # 获取用于免登的公司corp_id
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        data = {'corp_id': config.corp_id}
        if request.session.uid:
            request.session.uid = False
        if request.session.login:
            request.session.login = False
        return request.render('dingtalk_mc.auto_login_signup', data)

    @http.route('/web/dingtalk/mc/auto/login/action', type='http', auth='none', website=True, sitemap=False)
    @fragment_to_query_string
    def web_dingtalk_auto_signin_action(self, **kw):
        """
        通过获得的【免登授权码或者临时授权码】获取用户信息
        :param kw:
        :return:
        """
        auth_code = kw.get('authCode')
        logging.info(">>>免登授权码: %s", auth_code)
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        result = client.user.getuserinfo(auth_code)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            _logger.info(_("系统对应员工不存在!"))
            return self._do_err_redirect(_("系统对应员工不存在!"))
        _logger.info(">>>员工：{}正在尝试登录系统".format(employee.name))
        if not employee.ding_id:
            _logger.info(_("员工不存在钉钉ID，请维护后再试!"))
            return self._do_err_redirect(_("员工不存在钉钉ID，请维护后再试!"))
        if not employee.user_id:
            return self._do_err_redirect(_("你还没有关联系统用户，请联系管理员处理！"))
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
        return http.redirect_with_hash(url)

    def _do_err_redirect(self, errmsg):
        """
        返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        ding_error = request.params.copy()
        ding_error.update({
            'ding_error': errmsg
        })
        _logger.info("免密登陆失败,Error:{}".format(ding_error))
        return request.render('dingtalk_mc.dingtalk_mc_login_result_signup', ding_error)