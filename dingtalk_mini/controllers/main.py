# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from werkzeug.exceptions import BadRequest
from odoo import SUPERUSER_ID, api, http, _
from odoo import registry as registry_get
from odoo.addons.dingtalk_mc.controllers.login_controller import DingTalkMcLogin, OAuthController
from odoo.addons.auth_oauth.controllers.main import fragment_to_query_string
from odoo.addons.web.controllers.main import (login_and_redirect, ensure_db, set_cookie_and_redirect)
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class MiniOAuthController(OAuthController):

    # @http.route('/web/dingtalk/mini/auto/login', type='http', auth='public', website=True, csrf=False)
    # def web_dingtalk_mini_auto_login(self, **kw):
    #     """
    #     钉钉小程序免登入口
    #     :param kw:
    #     :return:
    #     """
    #     ensure_db()
    #     logging.info(">>>用户正在使用免登...")
    #     if request.session.uid:
    #         request.uid = request.session.uid
    #         try:
    #             context = request.env['ir.http'].webclient_rendering_context()
    #             response = request.render('web.webclient_bootstrap', qcontext=context)
    #             response.headers['X-Frame-Options'] = 'DENY'
    #             return response
    #         except AccessError as e:
    #             _logger.info("AccessError: {}".format(str(e)))
    #     # 获取用于免登的公司corp_id
    #     agent_id = kw.get('agentId')
    #     config = request.env['dingtalk.mini.config'].sudo().search([('agent_id', '=', agent_id)], limit=1)
    #     data = {'corp_id': config.corp_id}
    #     if request.session.uid:
    #         request.session.uid = False
    #     if request.session.login:
    #         request.session.login = False
    #     return request.render('dingtalk_mini.auto_login_signup', data)

    @http.route('/web/dingtalk/mini/auto/login_v2', type='http', auth='none', methods=['get', 'post'], csrf=False)
    # @fragment_to_query_string
    def web_dingtalk_mini_auto_signin(self, **kw):
        """
        通过获得的免登授权码获取用户信息后返回给钉钉小程序
        :param kw:
        :return:
        """

        auth_code = kw.get('authCode')
        logging.info(">>>免登授权码: %s", auth_code)
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        result = client.user.getuserinfo(auth_code)
        logging.info(">>>获取员工结果: %s", result)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            _logger.info(_("系统对应员工不存在!"))
            return self._do_err_redirect_dd(_("系统对应员工不存在!"))
        _logger.info(">>>员工：{}正在尝试登录系统".format(employee.name))
        if not employee.ding_id:
            _logger.info(_("员工不存在钉钉ID，请维护后再试!"))
            return self._do_err_redirect_dd(_("员工不存在钉钉ID，请维护后再试!"))
        if not employee.user_id:
            return self._do_err_redirect_dd(_("你还没有关联系统用户，请联系管理员处理！"))

        return_data = {
            'userId': result.userid,
            'userName': result.name,
        }
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>return_data', return_data)
        return json.dumps(return_data)

    @http.route('/web/dingtalk/mini/auto/login', type='http', auth='public', website=True, csrf=False)
    def web_dingtalk_mini_auto_login(self, **kw):
        """
        钉钉小程序免登入口
        :param kw:
        :return:
        """
        ensure_db()
        logging.info(">>>用户正在使用免登...")
        # if request.session.uid:
        #     request.uid = request.session.uid
        #     try:
        #         context = request.env['ir.http'].webclient_rendering_context()
        #         response = request.render('web.webclient_bootstrap', qcontext=context)
        #         response.headers['X-Frame-Options'] = 'DENY'
        #         return response
        #     except AccessError as e:
        #         _logger.info("AccessError: {}".format(str(e)))
        # 获取用于免登的公司corp_id
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        data = {'corp_id': config.corp_id}
        # if request.session.uid:
        #     request.session.uid = False
        # if request.session.login:
        #     request.session.login = False
        return request.render('dingtalk_mini.auto_login_signup', data)

    @http.route('/web/dingtalk/mini/auto/login/action', type='http', auth='none', methods=['get', 'post'], csrf=False)
    # @fragment_to_query_string
    def web_dingtalk_mini_auto_signin_v3(self, **kw):
        """
        通过获得的钉钉小程序免登授权码获取用户信息后auth登录odoo
        :param kw:
        :return:
        """

        auth_code = kw.get('authCode')
        logging.info(">>>免登授权码: %s", auth_code)
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        result = client.user.getuserinfo(auth_code)
        logging.info(">>>获取员工结果: %s", result)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            _logger.info(_("系统对应员工不存在!"))
            return self._do_err_redirect_dd(_("系统对应员工不存在!"))
        _logger.info(">>>员工：{}正在尝试登录系统".format(employee.name))
        if not employee.ding_id:
            _logger.info(_("员工不存在钉钉ID，请维护后再试!"))
            return self._do_err_redirect_dd(_("员工不存在钉钉ID，请维护后再试!"))
        if not employee.user_id:
            return self._do_err_redirect_dd(_("你还没有关联系统用户，请联系管理员处理！"))
        ensure_db()
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                credentials = env['res.users'].sudo().auth_oauth('dingtalk', employee.ding_id)
                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>credentials', credentials)
                cr.commit()
                url = '../odoo-web/odoo'
                resp = login_and_redirect(*credentials, redirect_url=url)
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                    resp.location = '/'
                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>resp', resp)
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

    @http.route('/dingtalk/eapp/login', type='http', auth='none', csrf=False)
    # @fragment_to_query_string
    def dingtalk_eapp_login_v1(self, **kw):
        """
        通过获得的钉钉小程序免登授权码获取用户信息后auth登录odoo
        :param kw:
        :return:
        """

        auth_code = kw.get('authCode')
        logging.info(">>>免登授权码: %s", auth_code)
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        result = client.user.getuserinfo(auth_code)
        logging.info(">>>获取员工结果: %s", result)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            _logger.info(_("系统对应员工不存在!"))
            return self._do_err_redirect_dd(_("系统对应员工不存在!"))
        _logger.info(">>>员工：{}正在尝试登录系统".format(employee.name))
        if not employee.ding_id:
            _logger.info(_("员工不存在钉钉ID，请维护后再试!"))
            return self._do_err_redirect_dd(_("员工不存在钉钉ID，请维护后再试!"))
        if not employee.user_id:
            return self._do_err_redirect_dd(_("你还没有关联系统用户，请联系管理员处理！"))
        dd_info = {'dd_user_info':
                   {'Userid': result.userid,
                    'Name': result.name,
                    'Avatar': '',
                    },
                   'token': client.get_access_token().access_token
                   }
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>dd_user_info', dd_info)
        return json.dumps(dd_info)

        # ensure_db()
        # dbname = request.session.db
        # if not http.db_filter([dbname]):
        #     return BadRequest()
        # registry = registry_get(dbname)
        # with registry.cursor() as cr:
        #     try:
        #         env = api.Environment(cr, SUPERUSER_ID, {})
        #         credentials = env['res.users'].sudo().auth_oauth('dingtalk', employee.ding_id)
        #         print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>credentials',credentials)
        #         cr.commit()
        #         url = '../odoo-web/odoo'
        #         resp = login_and_redirect(*credentials, redirect_url=url)
        #         if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
        #             resp.location = '/'
        #         print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>resp',resp)
        #         return resp
        #     except AttributeError:
        #         _logger.error(">>>未在数据库'%s'上安装auth_signup：oauth注册已取消。" % (dbname,))
        #         url = "/web/login?oauth_error=1"
        #     except AccessDenied:
        #         _logger.info('>>>DingTalk-OAuth2: 访问被拒绝，在存在有效会话的情况下重定向到主页，而未设置Cookie')
        #         url = "/web/login?oauth_error=3"
        #         redirect = werkzeug.utils.redirect(url, 303)
        #         redirect.autocorrect_location_header = False
        #         return redirect
        #     except Exception as e:
        #         _logger.exception("OAuth2: %s" % str(e))
        #         url = "/web/login?oauth_error=2"

    def _do_err_redirect_dd(self, errmsg):
        """
        返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        ding_error = {}
        ding_error.update({
            'ding_error': errmsg
        })
        _logger.info("免密登陆失败,Error:{}".format(ding_error))
        return request.render('dingtalk_mini.dingtalk_mini_login_result_signup', ding_error)
