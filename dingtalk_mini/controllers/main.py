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

    @http.route('/miniapp/dd/login', type='http', auth='none', methods=['get', 'post'], csrf=False)
    # @fragment_to_query_string
    def miniapp_dd_login_v1(self, **kw):
        """
        通过获得的钉钉小程序免登授权码获取用户信息后auth登录odoo
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        auth_code = params_data.get('code')
        logging.info(">>>免登授权码: %s", auth_code)
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        result = client.user.getuserinfo(auth_code)
        logging.info(">>>获取员工结果: %s", result)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            _logger.info(_("系统对应员工不存在!"))
            return json.dumps({'state': False, 'msg': '系统对应员工不存在!'})
        _logger.info(">>>员工：{}正在尝试登录系统".format(employee.name))
        if not employee.ding_id:
            _logger.info(_("员工不存在钉钉ID，请维护后再试!"))
            return json.dumps({'state': False, 'msg': '员工不存在钉钉ID，请维护后再试!'})
        if not employee.user_id:
            return json.dumps({'state': False, 'msg': '你还没有关联系统用户，请联系管理员处理！'})
        dd_info = {'dd_user_info': {'Userid': result.userid,
                                    'Name': result.name,
                                    'Avatar': '',
                                    },
                   'token': client.get_access_token().access_token
                   }
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>dd_user_info', dd_info)
        return json.dumps(dd_info)

    @http.route('/miniapp/dd/authenticate', type='http', auth='none', methods=["GET", "POST"], csrf=False, website=True)
    def dingtalk_authenticate(self, **kw):

        params_data = request.params.copy()
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>params_data', params_data)
        auth_code = params_data.get('code')

        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        result = client.user.getuserinfo(auth_code)
        domain = [('ding_id', '=', result.userid), ('company_id', '=', config.company_id.id)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if employee:
            userid = result.userid
            uid = request.session.authenticate(request.session.db, employee.user_id.login, userid)
            request.session.dd_user_id = userid
            if uid:
                values = {'status': 'success', 'dd_user_id': userid, 'uid': uid, 'name': result.name,
                          'session_id': request.session.sid}
            else:
                return json.dumps({'status': 'error', 'errmsg': u'您没有绑定Odoo用户,请联系管理员！'})
            _logger.info("values:" + str(values))
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>values', values)
            return json.dumps(values)
        else:
            return json.dumps({'status': 'error', 'errmsg': u'您没有绑定Odoo用户,请联系管理员！'})


class MiniAppController(http.Controller):

    @http.route('/miniapp/dd/token/refresh', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def dingtalk_auth_refresh(self, **kw):
        """
        刷新token
        :param kw:
        :return:
        """
        config = request.env['dingtalk.mc.config'].sudo().search([('m_login', '=', True)], limit=1)
        client = dt.get_client(request, dt.get_dingtalk_config(request, config.company_id))
        return json.dumps({'token': client.get_access_token().access_token})

    @http.route('/miniapp/dd/users/menus', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def dingtalk_eapp_users_menus(self, **kw):
        """
        初始化菜单
        :param kw:
        :return:
        """
        menu = [{}]
        return json.dumps(menu)

    @http.route('/miniapp/dd/users/groups', type='json', auth='none', methods=['get', 'post'], csrf=False)
    def dingtalk_eapp_users_groups(self, **kw):
        """
        初始化权限
        :param kw:
        :return:
        """
        return json.dumps([])

    @http.route('/miniapp/dd/test', type='http', auth='public', methods=['get', 'post'], cors='*', csrf=False, website=True)
    # 接受外部系统推送过来的凭证信息并新增凭证
    def create_voucher(self, *args, **kw):
        '''接受推送的凭证'''

        params_data = request.params.copy()
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>params_data', params_data)

        # data = request.data
        # print('>>>>>>>>>>>>>>>>>>>>>>>>>data',data)
        # data = json.loads(data)['postdata']
        # 检查权限
        # self.env = request.env
        # user = self._check_access(loginUser, pw, mark)
        # # 检查凭证逻辑
        # self._check_voucher_logic(data)
        # # 构建符合格式的凭证
        # voucher = self._build_voucher(autoCreate, data, user)
        # v = self.env['accountcore.voucher'].sudo().create(voucher)
        # return {"uniqueNumber": v.uniqueNumber}
        # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>name',name)
        return json.dumps({'status': 'success', 'message': u'数据已成功录入！'})

    # 检查权限
    @http.route('/', type='json', auth='none', methods=['get', 'post'], csrf=False)
    def dingtalk_eapp_users_menus(self, idField, limit, orderBy, page, pageable, params, **kw):
        """
        通用搜索方法
        :param kw:
        :return:
        http://cnongood.vaiwan.comurl/?idField=id&limit=20&orderBy=id&page=1&pageable=true&params={"name":"5555"}&sort=desc

http://cnongood.vaiwan.comurl/?idField=id&limit=20&orderBy=id&page=1&pageable=true&params=%7B%22name%22%3A%225555%22%7D&sort=desc
        """
        menu = [{}]
        return json.dumps(menu)
