# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import http, _
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.http import request
from urllib.parse import quote
import hmac
import odoo

_logger = logging.getLogger(__name__)


class DinDinLogin(Home, http.Controller):

    @http.route('/web/dindin_login', type='http', auth='public', website=True, sitemap=False)
    def web_dindin_login(self, *args, **kw):
        """
        主页点击钉钉扫码登录route 将返回到扫码页面
        :param args:
        :param kw:
        :return:
        """
        values = request.params.copy()
        return request.render('dindin_login.signup', values)

    @http.route('/dindin_login/get_url', type='http', auth="none")
    def get_url(self, **kw):
        """
        拼接访问钉钉的验证用户的url
        :param kw:
        :return:
        """
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
        if not code:
            return self._do_err_redirect("错误的访问地址,请输入正确的访问地址")
        logging.info(">>>获取的code为：{}".format(code))
        result = self.getUserInfobyDincode(code)
        logging.info(">>>result:{}".format(result))
        if not result['state']:
            logging.info(result['msg'])
            return self._do_err_redirect(result['msg'])
        return self._do_post_login(result['user'], redirect)

    def _do_post_login(self, user, redirect):
        """
        所有的验证都结束并正确后，需要界面跳转到主界面
        :param user:  user-Object
        :param redirect:
        :return:
        """
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        old_uid = request.uid
        # 解密钉钉登录密码
        logging.info(u'>>>:解密钉钉登录密码')
        password = base64.b64decode(user.din_password)
        password = password.decode(encoding='utf-8', errors='strict')
        logging.info(">>>d1")
        if password == '' or not password:
            logging.info(">>>d2")
            return self._do_err_redirect("用户:'{}'无法进行登录,请修改该用户登录密码并关联员工!".format(user.login))
        if password == '123456':
            logging.info(">>>d3")
            user.sudo().password = '123'
            user.sudo()._set_password()
            logging.info(">>>d4")
            return self._do_err_redirect("'{}'密码已重置为123,再次扫描进行登录!".format(user.login))
        logging.info(">>>d5")
        uid = request.session.authenticate(request.session.db, user.login, password)
        logging.info(">>>d6")
        logging.info(u'>>>:uid: {}'.format(uid))
        if uid is not False:
            request.params['login_success'] = True
            if not redirect:
                redirect = '/web'
            logging.info(u'>>>:用户{}登录成功,将跳转到主界面'.format(user.login))
            return http.redirect_with_hash(redirect)
        request.uid = old_uid
        return self._do_err_redirect("用户不存在或用户信息错误,无法完成登录,请联系管理员")

    def getUserInfobyDincode(self, d_code):
        """
        根据返回的临时授权码获取用户信息
        :param d_code:
        :return:
        """
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'getuserinfo_bycode')]).value
        login_appid = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appid')
        key = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_login_appsecret')
        current_milli_time = lambda: int(round(time.time() * 1000))
        msg = str(current_milli_time())
        # ------------------------
        # 签名
        # ------------------------
        signature = hmac.new(key.encode('utf-8'), msg.encode('utf-8'),
                             hashlib.sha256).digest()
        signature = quote(base64.b64encode(signature), 'utf-8')
        data = {
            'tmp_auth_code': d_code
        }
        headers = {'Content-Type': 'application/json'}
        new_url = "{}signature={}&timestamp={}&accessKey={}".format(url, signature, msg, login_appid)
        try:
            result = requests.post(url=new_url, headers=headers, data=json.dumps(data), timeout=15)
            result = json.loads(result.text)
            logging.info(">>>扫码登录获取用户信息返回结果{}".format(result))
            if result.get('errcode') == 0:
                user_info = result.get('user_info')
                # 通过unionid获取userid并得到系统的user
                # userid = self.getUseridByUnionid(user_info.get('unionid'))
                employee = request.env['hr.employee'].sudo().search([('din_unionid', '=', user_info.get('unionid'))])
                if employee:
                    if employee.user_id:
                        return {'state': True, 'user': employee.user_id}
                    else:
                        return {'state': False, 'msg': "员工'{}'没有关联系统用户，请联系管理员维护!".format(employee.name)}
                else:
                    return {'state': False, 'msg': "钉钉员工'{}'在系统中不存在,请联系管理员维护!".format(user_info.get('nick'))}
            else:
                return {'state': False, 'msg': '扫码登录获取用户信息失败，详情为:{}'.format(result.get('errmsg'))}
        except ReadTimeout:
            return {'state': False, 'msg': '网络连接超时'}

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

    def _do_err_redirect(self, errmsg):
        """
        返回到钉钉扫码界面并返回信息errmsg
        :param errmsg: 需要返回展示的信息
        :return:
        """
        err_values = request.params.copy()
        err_values['error'] = _(errmsg)
        http.redirect_with_hash('/web/login')
        return request.render('dindin_login.signup', err_values)
