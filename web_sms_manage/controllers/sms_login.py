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
import datetime
import json
import logging
import random

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from qcloudsms_py import SmsSingleSender
from werkzeug.exceptions import BadRequest

from odoo import SUPERUSER_ID, _, api, http
from odoo import registry as registry_get
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.web.controllers.main import (Home, ensure_db,
                                              set_cookie_and_redirect)
from odoo.http import request

_logger = logging.getLogger(__name__)


class OdooSmsController(Home, http.Controller):

    @http.route('/web/login/sms', type='http', auth='public', website=True, sitemap=False)
    def web_odoo_sms_login(self, *args, **kw):
        """
        短信登录入口,点击后返回到验证码界面
        :param args:
        :param kw:
        :return:
        """
        values = request.params.copy()
        services = request.env['sms.service.config'].sudo().search([('state', '=', 'open')])
        if services and len(services) == 1:
            values['code_maxlength'] = services[0].code_length  # 验证码最大长度
        else:
            values['code_maxlength'] = 6  # 验证码默认最大长度
        return request.render('odoo_sms.login_signup', values)

    @http.route('/web/odoo/send/sms/by/phone', type='http', auth="none")
    def web_send_sms_code_by_phone(self, **kw):
        """
        向手机号码发送验证码
        :param kw:
        :return:
        """
        user_phone = request.params['user_phone']
        # 验证是否存在系统用户
        users = request.env['res.users'].sudo().search([('oauth_uid', '=', user_phone)])
        if not users:
            return json.dumps({'state': False, 'msg': "该手机号码未绑定系统用户，请注册！"})
        # 判断要使用的短信平台，获取配置中已开启的短信平台服务
        services = request.env['sms.service.config'].sudo().search([('state', '=', 'open')])
        result = False
        if not services:
            return json.dumps({'state': False, 'msg': "短信服务平台已关闭,请联系管理员处理."})
        for service in services:
            if service.sms_type == 'tencent':
                # 使用腾讯云短信平台
                logging.info("正在使用腾讯云短信平台")
                result = self.send_code_by_tencent(service, user_phone)
                logging.info(result)
                if result['state']:
                    break
            elif service.sms_type == 'ali':
                logging.info("正在使用阿里云短信平台")
                result = self.send_code_by_aliyun(service, user_phone)
                logging.info(result)
                if result['state']:
                    break
        if result['state']:
            return json.dumps({"state": True, 'msg': "验证码已发送，请注意查收短信！"})
        else:
            return json.dumps({"state": False, 'msg': result['msg']})

    def send_code_by_tencent(self, service, user_phone):
        """
        使用注意：需要配合在腾讯云的短息模板中配置两个可自定义的内容，{1}：为验证码，{2}：为有效时长
        使用腾讯云平台往指定手机发送验证码
        :param service:
        :param user_phone:
        :return:
        """
        template_id, sms_sign, timeout = self._get_config_template(service, 'login')
        if not template_id or not sms_sign or not timeout:
            return {"state": False, 'msg': "在(短信服务配置)中没有找到可用于(登录时发送验证码)的模板,请联系管理员设置！"}
        s_sender = SmsSingleSender(service.app_id, service.app_key)
        # 传递短信模板参数{1}为验证码， {2}为有效时长
        params = [self.generate_random_numbers(service.code_length), timeout]
        try:
            result = s_sender.send_with_param(86, user_phone, template_id, params, sign=sms_sign, extend="", ext="")
            logging.info("tencent-sms-result:{}".format(result))
            if result['result'] == 0:
                record = self.create_record(user_phone, service, result['sid'], params[0], timeout)
                return {"state": True}
            else:
                return {"state": False, 'msg': "发送验证码失败!,Error:{}".format(result['errmsg'])}
        except Exception as e:
            return {"state": False, 'msg': "腾讯云发送验证码失败,Error:{}".format(str(e))}

    def send_code_by_aliyun(self, service, user_phone):
        """
        利用阿里云短息平台进行发送验证码； 注意只能传递一个传递及验证码
        :param service:
        :param user_phone:
        :return:
        """
        client = AcsClient(service.app_id, service.app_key, 'default')
        com_request = CommonRequest()
        com_request.set_accept_format('json')
        com_request.set_domain("dysmsapi.aliyuncs.com")
        com_request.set_method('POST')
        com_request.set_protocol_type('https')
        com_request.set_version('2017-05-25')
        com_request.set_action_name('SendSms')
        template_id, sms_sign, timeout = self._get_config_template(service, 'login')
        if not template_id or not sms_sign or not timeout:
            return {"state": False, 'msg': "在(短信服务配置)中没有找到可用于(登录时发送验证码)的模板,请联系管理员设置！"}
        com_request.add_query_param('PhoneNumbers', user_phone)
        com_request.add_query_param('SignName', sms_sign)
        com_request.add_query_param('TemplateCode', template_id)

        param_data = {
            'name': 'sms_sign',
            'code': self.generate_random_numbers(service.code_length)
        }
        param_json = json.dumps(param_data)

        com_request.add_query_param('TemplateParam', param_json)
        try:
            cli_response = client.do_action_with_exception(com_request)
            cli_res = json.loads(str(cli_response, encoding='utf-8'))
            logging.info("ali-sms-result: {}".format(cli_res))
            if cli_res['Code'] == 'OK':
                record = self.create_record(user_phone, service, cli_res['RequestId'], param_data['code'], timeout)
                return {"state": True}
            else:
                return {"state": False, 'msg': "发送验证码失败!,Error:{}".format(cli_res['Message'])}
        except Exception as e:
            return {"state": False, 'msg': "阿里云发送验证码失败,Error:{}".format(str(e))}

    def create_record(self, user_phone, service, sms_sid, code, timeout):
        """
        创建短信发送记录
        :param user_phone: 用户登录手机
        :param service: 短信平台
        :param sms_sid: 标识唯一码，可通过改唯一码查询通知结果
        :param code:  验证码
        :param timeout:  超时时长
        :return:
        """
        users = request.env['res.users'].sudo().search([('oauth_uid', '=', user_phone)])
        record = request.env['sms.verification.record'].sudo().create({
            'service_id': service.id,
            'user_id': users[0].id if users else False,
            'phone': user_phone,
            'sid': sms_sid,
            'code': code,
            'timeout': timeout,
        })
        return record

    @http.route('/web/check/sms/verification/code', type='http', auth="none")
    def check_verification_code(self, **kw):
        """
        点击登录按钮执行的操作
        :param kw:
        :return:
        """
        phone = request.params['phone']
        code = request.params['code']
        logging.info("-手机号码:{},验证码:{}进行登录验证".format(phone, code))
        domain = [('phone', '=', phone), ('code', '=', code)]
        records = request.env['sms.verification.record'].sudo().search(domain)
        if not records:
            return json.dumps({'state': False, 'msg': "验证码不存在,请重新输入！"})
        # 检查时效
        for record in records:
            if datetime.datetime.now() > record.end_time:
                record.sudo().write({'state': 'invalid'})
                return json.dumps({'state': False, 'msg': "验证码已失效！请重新获取!"})
        records.sudo().write({'state': 'invalid'})
        return self._web_post_login(phone)

    def _web_post_login(self, phone):
        """
        验证手机并登陆系统
        :param phone:
        :return:
        """
        dbname = request.session.db
        if not http.db_filter([dbname]):
            return BadRequest()
        context = {}
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth_sms('sms', phone)
                cr.commit()
                url = '/web'
                uid = request.session.authenticate(*credentials)
                if uid is not False:
                    request.params['login_success'] = True
                    return json.dumps({'state': True, 'msg': "登录成功"})
            except Exception as e:
                # signup error
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"
        return set_cookie_and_redirect(url)

    def _get_config_template(self, service, tem_type):
        """
        获取可发送验证码的短信模板、签名、超时时长
        :param service:
        :param tem_type:
        :return:
        """
        template_id = 0  # 短信模板ID，需要在短信控制台中申请
        sms_sign = ""  # 短信签名
        timeout = ""  # 超时时长 {2}
        # 获取可发送验证码的短信模板和签名
        for template in service.template_ids:
            if template.used_for == tem_type:
                template_id = template.template_id
                sms_sign = template.sign_name
                timeout = template.timeout
        return template_id, sms_sign, timeout

    def generate_random_numbers(self, length_size):
        """
        生成指定位数的随机数字字符串
        :param length_size:
        :return:
        """
        numbers = ""
        for i in range(length_size):
            ch = chr(random.randrange(ord('0'), ord('9') + 1))
            numbers += ch
        return numbers
