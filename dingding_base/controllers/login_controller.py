# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import functools
import json
import logging
import requests
import werkzeug
from werkzeug.exceptions import BadRequest
from odoo import SUPERUSER_ID, api, http, _
from odoo import registry as registry_get
from odoo.addons.auth_oauth.controllers.main import OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import (login_and_redirect, ensure_db, set_cookie_and_redirect)
from odoo.http import request

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


class OAuthController(Controller):

    @http.route('/dingding/auto/login/in', type='http', auth='none')
    def dingding_auto_login(self, **kw):
        """
        免登入口
        :param kw:
        :return:
        """
        logging.info(">>>用户正在使用免登...")
        data = {'corp_id': request.env['ir.config_parameter'].sudo().get_param('dingding_base.corp_id')}
        return request.render('dingding_base.auto_login_signup', data)

    @http.route('/dingding/auto/login', type='http', auth='none')
    @fragment_to_query_string
    def auto_signin(self, **kw):
        """
        通过获得的【免登授权码或者临时授权码】获取用户信息
        :param kw:
        :return:
        """
        auth_code = kw.get('authCode')
        logging.info(">>>免登授权码: %s", auth_code)
        user_id = self.get_userid_by_auth_code(auth_code)
        if not user_id:
            return self._do_err_redirect("钉钉免登失败！具体原因是无法获取用户code，请检查后台IP是否发生变化!")
        employee = request.env['hr.employee'].sudo().search([('ding_id', '=', user_id)], limit=1)
        if not employee:
            return self._do_err_redirect("系统对应员工不存在!")
        logging.info(">>>员工{}正在尝试登录系统".format(employee.name))
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        context = {}
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth_dingtalk("dingtalk", employee.sudo().ding_id)
                cr.commit()
                url = '/web'
                uid = request.session.authenticate(*credentials)
                if uid is not False:
                    logging.info(">>>员工{}登录成功".format(employee.sudo().name))
                    # request.params['login_success'] = False
                    return set_cookie_and_redirect(url)
            except Exception as e:
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(url)

    def get_userid_by_auth_code(self, auth_code):
        """
        根据返回的免登授权码获取用户userid
        :param auth_code:
        :return:
        """
        url, token = request.env['dingding.parameter'].sudo().get_parameter_value_and_token('get_userid')
        url = "{}?access_token={}&code={}".format(url, token, auth_code)
        try:
            result = requests.get(url=url, timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                return result.get('userid')
            raise BadRequest(result)
        except Exception as e:
            return {'state': False, 'msg': "异常信息:{}".format(str(e))}

    def _do_err_redirect(self, errmsg):
        """
        返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        err_values = request.params.copy()
        err_values['message'] = _(errmsg)
        return request.render('dingding_base.auto_login_message_signup', err_values)


class DingDingLogin(Home, http.Controller):
    """
    钉钉扫码登录以及账号登录功能Controller
    """

    @http.route('/web/dingding/login', type='http', auth='public', website=True, sitemap=False)
    def web_dingding_login(self, *args, **kw):
        """
        主页点击钉钉扫码登录route 将返回到扫码页面
        :param args:
        :param kw:
        :return:
        """
        values = request.params.copy()
        return request.render('dingding_base.login_signup', values)

    @http.route('/web/dingding/account/login', type='http', auth='public', website=True, sitemap=False)
    def web_dingding_account_login(self, *args, **kw):
        """
        主页点击钉钉账号密码登录 重定向到钉钉登录页
        :param args:
        :param kw:
        :return:
        """
        url = request.env['dingding.parameter'].sudo().get_parameter_value('sns_authorize')
        appid = request.env['ir.config_parameter'].sudo().get_param('dingding_base.din_login_appid')
        redirect_url = '{}dingding/login/action'.format(request.httprequest.host_url)
        new_url = '{}appid={}&response_type=code&scope=snsapi_login&state=STATE&redirect_uri={}'.format(url, appid, redirect_url)
        return http.redirect_with_hash(new_url)

    @http.route('/dingding/login/get_url', type='http', auth="none")
    def get_login_url(self, **kw):
        """
        拼接访问钉钉的验证用户的url
        :param kw:
        :return:
        """
        url = request.env['dingding.parameter'].sudo().get_parameter_value('sns_authorize')
        login_appid = request.env['ir.config_parameter'].sudo().get_param('dingding_base.din_login_appid')
        # 获取传递过来当前的url和端口信息
        callback_url = "{}/dingding/login/action".format(request.params['local_url'])
        encode_url = "{}appid={}&response_type=code&scope=snsapi_login&redirect_uri={}".format(url, login_appid, callback_url)
        return json.dumps({"encode_url": encode_url, 'callback_url': callback_url})

    @http.route('/dingding/login/action', type='http', auth="none")
    def action_ding_login(self, redirect=None, **kw):
        """
        接受到钉钉返回的数据时进入此方法
        1. 根据返回的临时授权码获取员工的信息
        2. 查找本地员工对应的关联系统用户。
        3. 界面跳转
        :param redirect:
        :param kw:
        :return:
        """
        code = request.params['code']
        logging.info(">>>扫码登录code为：{}".format(code))
        result = request.env['dingding.api.tools'].sudo().get_user_info_by_code(code)
        logging.info(">>>result:{}".format(result))
        if not result['state']:
            logging.info(result['msg'])
            return self._do_err_redirect(result['msg'])
        return self._do_post_login(result['employee'], redirect)

    def _do_post_login(self, employee, redirect):
        """
        所有的验证都结束并正确后，需要界面跳转到主界面
        :param employee:  employee
        :param redirect:
        :return:
        """
        ensure_db()
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        context = {}
        registry = registry_get(dbname)
        oauth_uid = employee.sudo().ding_id
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth_dingtalk("dingtalk", oauth_uid)
                cr.commit()
                url = '/web' if not redirect else redirect
                uid = request.session.authenticate(*credentials)
                if uid:
                    return http.redirect_with_hash(url)
                else:
                    self._do_err_redirect("登录失败")
            except Exception as e:
                self._do_err_redirect("登录失败,原因为:{}".format(str(e)))

    def _do_err_redirect(self, errmsg):
        """
        返回到钉钉扫码界面并返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        err_values = request.params.copy()
        err_values['error'] = _(errmsg)
        http.redirect_with_hash('/web/login')
        return request.render('dingding_base.login_signup', err_values)

