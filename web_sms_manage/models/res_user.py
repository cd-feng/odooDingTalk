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
import base64
import json
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from qcloudsms_py import SmsSingleSender
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.constrains('oauth_uid')
    def constrains_login_phone(self):
        """
        检查手机是否重复
        :return:
        """
        for res in self:
            if res.oauth_uid:
                users = self.env['res.users'].sudo().search([('oauth_uid', '=', res.oauth_uid)])
                if len(users) > 1:
                    raise UserError("抱歉！{}手机号码（令牌）已被'{}'占用,请解除或更换号码!".format(res.oauth_uid, users[0].name))

    @api.model
    def auth_oauth_sms(self, provide_id, user_phone):
        if provide_id == 'sms':
            domain = ['|', ('mobile_phone', '=', user_phone), ('work_phone', '=', user_phone)]
            employee = self.env['hr.employee'].sudo().search(domain)
            user_ids = employee.user_id
        else:
            user_ids = self.search([('oauth_provider_id', '=', provide_id), ('oauth_uid', '=', user_phone)])
        _logger.info("user: %s", user_ids)
        if not user_ids or len(user_ids) > 1:
            raise AccessDenied()
        return (self.env.cr.dbname, user_ids[0].login, user_phone)

    @api.model
    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            res = self.sudo().search([('id', '=', self.env.uid)])
            if not res:
                raise

    # def _set_password(self):
    #     """
    #     修改密码后，短信通知到用户
    #     :return:
    #     """
    #     for user in self:
    #         user.sudo().write({'odoo_sms_token': base64.b64encode(user.password.encode('utf-8'))})
    #         if user.login_phone:
    #             result = self.send_change_password_sms(user.login, user.password, user.login_phone)
    #             if not result['state']:
    #                 raise ValidationError("抱歉，系统发送修改密码通知短信不成功,请检查原因；Error:{}".format(result['msg']))
    #     super(ResUsers, self)._set_password()

    def send_change_password_sms(self, login, password, phone):
        """
        发送修改密码通知短信
        :param login:
        :param password:
        :param phone:
        :return:
        """
        services = self.env['sms.service.config'].sudo().search([('state', '=', 'open')])
        if not services:
            return {'state': False, 'msg': "短信服务平台已关闭,请联系管理员处理"}
        result = False
        for service in services:
            if service.sms_type == 'tencent':
                result = self._send_change_pwd_sms_by_tencent(login, password, service, phone)
                logging.info(result)
                if result['state']:
                    break
            elif service.sms_type == 'ali':
                logging.info("正在使用阿里云短信平台")
                result = self._send_change_pwd_sms_by_aliyun(login, password, service, phone)
                logging.info(result)
                if result['state']:
                    break
        if result['state']:
            return {"state": True, 'msg': "通知短信已发送"}
        else:
            return {"state": False, 'msg': result['msg']}

    def _send_change_pwd_sms_by_tencent(self, login, password, service, phone):
        """
        腾讯云发送修改密码通知短信
        腾讯云短信通知模板: "你好: 你的账户信息已发生改变，新的账户信息为：用户名：{1}，密码：{2}，请及时登录系统并进行修改！"
        :param login:
        :param password:
        :param service:
        :param phone:
        :return:
        """
        template_id, sms_sign, timeout = self._get_sms_config_template(service, 'change_pwd')
        if not template_id or not sms_sign or not timeout:
            return {"state": False, 'msg': "在(短信服务配置)中没有找到可用于(修改密码通知模板)的模板,请联系管理员设置！"}
        s_sender = SmsSingleSender(service.app_id, service.app_key)
        params = [login, password]
        try:
            result = s_sender.send_with_param(86, phone, template_id, params, sign=sms_sign, extend="", ext="")
            logging.info("tencent-sms-change-pwd:{}".format(result))
            if result['result'] == 0:
                return {"state": True}
            else:
                return {"state": False, 'msg': "腾讯云发送修改密码短信失败!,Error:{}".format(result['errmsg'])}
        except Exception as e:
            return {"state": False, 'msg': "腾讯云发送修改密码短信失败,Error:{}".format(str(e))}

    def _send_change_pwd_sms_by_aliyun(self, login, password, service, phone):
        """
        通过阿里云发送修改密码通知短信
        短信模板为： "你好: 你的账户信息已发生改变，新的账户信息为：用户名：${name}，密码：${pwd}，请及时登录系统查看或进行修改！"
        :param login:
        :param password:
        :param service:
        :param phone:
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
        template_id, sms_sign, timeout = self._get_sms_config_template(service, 'change_pwd')
        if not template_id or not sms_sign or not timeout:
            return {"state": False, 'msg': "在(短信服务配置)中没有找到可用于(登录时发送验证码)的模板,请联系管理员设置！"}
        com_request.add_query_param('PhoneNumbers', phone)
        com_request.add_query_param('SignName', sms_sign)
        com_request.add_query_param('TemplateCode', template_id)
        param_data = {
            'name': login,
            'pwd': password
        }
        param_json = json.dumps(param_data)
        com_request.add_query_param('TemplateParam', param_json)
        try:
            cli_response = client.do_action_with_exception(com_request)
            cli_res = json.loads(str(cli_response, encoding='utf-8'))
            logging.info("ali-sms-result: {}".format(cli_res))
            if cli_res['Code'] == 'OK':
                return {"state": True}
            else:
                return {"state": False, 'msg': "阿里云发送修改密码短信失败!,Error:{}".format(cli_res['Message'])}
        except Exception as e:
            return {"state": False, 'msg': "阿里云发送修改密码短信失败,Error:{}".format(str(e))}

    @api.model
    def _get_sms_config_template(self, service, tem_type):
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