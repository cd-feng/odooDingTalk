# -*- coding: utf-8 -*-
import base64
import json
import logging
import random
import requests
from requests import ReadTimeout
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AutoLoginController(http.Controller):

    @http.route('/dingding/auto/login/in', type='http', auth='none')
    def dingding_auto_login(self, **kw):
        """
        免登入口
        :param kw:
        :return:
        """
        logging.info("检测到用户使用免登...")
        data = {'corp_id': request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')}
        return request.render('dindin_login.dingding_auto_login', data)

    @http.route('/dingding/auto/login', type='http', auth='none')
    def auth(self, **kw):
        """
        通过得到的临时授权码获取用户信息
        :param kw:
        :return:
        """
        authCode = kw.get('authCode')
        logging.info("临时授权码：{}".format(authCode))
        if authCode:
            userid = self.get_user_info_by_auth_code(authCode)
            logging.info(">>>获取的user_info为：{}".format(userid))
            employee = request.env['hr.employee'].sudo().search([('din_id', '=', userid)])
            if employee:
                user = employee.user_id
                if user:
                    # 解密钉钉登录密码
                    logging.info(u'>>>:解密钉钉登录密码')
                    password = base64.b64decode(user.din_password)
                    password = password.decode(encoding='utf-8', errors='strict')
                    request.session.authenticate(request.session.db, user.login, password)
                    return http.local_redirect('/web')
                else:
                    # 自动注册
                    password = str(random.randint(100000, 999999))
                    fail = request.env['res.users'].sudo().create_user_by_employee(employee.id, password)
                    if not fail:
                        return http.local_redirect('/dingding/auto/login/in')
                return http.local_redirect('/web/login')
            return http.local_redirect('/web/login')

    def get_user_info_by_auth_code(self, auth_code):
        """
        根据返回的临时授权码获取用户信息
        :param auth_code:
        :return:
        """
        url = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'get_userid')]).value
        token = request.env['ali.dindin.system.conf'].sudo().search([('key', '=', 'token')]).value
        url = "{}?access_token={}&code={}".format(url, token, auth_code)
        try:
            result = requests.get(url=url, timeout=5)
            result = json.loads(result.text)
            logging.info(">>>钉钉登录获取用户信息返回结果{}".format(result))
            if result.get('errcode') != 0:
                raise Exception('钉钉接口错误:' + result.get('errmsg') + ' | 接口地址:' + url)
            else:
                return result.get('userid')
        except ReadTimeout:
            raise Exception("免登超时！")
