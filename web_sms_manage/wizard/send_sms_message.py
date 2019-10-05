# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import json
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from qcloudsms_py import SmsSingleSender, SmsMultiSender
from werkzeug.exceptions import BadRequest

_logger = logging.getLogger(__name__)


class SendSmsMessage(models.TransientModel):
    _name = 'send.sms.message'
    _description = "发送通知短信"

    emp_ids = fields.Many2many('hr.employee', string=u'员工', required=True)
    message = fields.Text(string=u'消息内容', required=True, help="要发送的消息内容")

    
    def send_sms_message(self):
        """
        发送短信到收信人
        :return:
        """
        self.ensure_one()
        # 检查员工工作手机号和封装
        phone_str = ''
        phone_arr = list()
        number = 0
        for emp in self.emp_ids:
            if not emp.mobile_phone:
                raise UserError("员工:{}不存在工作手机号，无法发送，请更正！".format(emp.name))
            if number == 0:
                phone_str = emp.mobile_phone
                number += 1
            else:
                phone_str = phone_str + ',{}'.format(emp.mobile_phone)
            phone_arr.append(emp.mobile_phone)
        # 判断要使用的短信平台，获取配置中已开启的短信平台服务
        services = self.env['sms.service.config'].sudo().search([('state', '=', 'open')])
        if not services:
            raise UserError("无可用的短信服务平台,请联系管理员处理.")
        result = False
        for service in services:
            if service.sms_type == 'tencent':
                # 使用腾讯云短信平台
                logging.info("正在使用腾讯云短信平台")
                result = self.send_message_by_tencent(service, phone_arr)
                logging.info(result)
                if result['state']:
                    break
            elif service.sms_type == 'ali':
                logging.info("正在使用阿里云短信平台")
                result = self.send_message_by_ali(service, phone_str)
                logging.info(result)
                if result['state']:
                    break
        if not result['state']:
            raise UserError(result['msg'])
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def send_message_by_tencent(self, service, phone_arr):
        """
        通过腾讯云发送消息至用户
        短信模板示例： 您有新的消息通知：发起人：{1}，内容为：{2}，请及时登录系统处理！
        :param service: 
        :param phone_arr:
        :return: 
        """
        template_id, sms_sign, timeout = self._get_config_template(service, 'send_message')
        if not template_id or not sms_sign or not timeout:
            return {"state": False, 'msg': "在(短信服务配置)中没有找到可用于(用于Odoo通知消息)的模板,请联系管理员设置！"}
        msender = SmsMultiSender(service.app_id, service.app_key)
        # 传递短信模板参数{1}为验证码， {2}为有效时长
        params = [self.env.user.name, self.message]
        try:
            result = msender.send_with_param(86, phone_arr, template_id, params, sign=sms_sign, extend="", ext="")
            logging.info("tencent-sms-result:{}".format(result))
            if result['result'] == 0:
                return {"state": True}
            else:
                return {"state": False, 'msg': "发送消息失败!,Error:{}".format(result['errmsg'])}
        except Exception as e:
            return {"state": False, 'msg': "发送消息失败,Error:{}".format(str(e))}

    @api.model
    def send_message_by_ali(self, service, user_phone):
        """
        通过阿里云发送消息至用户
        短信模板示例： 您有新的消息通知：发起人：${username}，内容为：${message}，请及时登录系统处理！
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
        template_id, sms_sign, timeout = self._get_config_template(service, 'send_message')
        if not template_id or not sms_sign or not timeout:
            return {"state": False, 'msg': "在(短信服务配置)中没有找到可用于(用于Odoo通知消息)的模板,请联系管理员设置！"}
        com_request.add_query_param('PhoneNumbers', user_phone)
        com_request.add_query_param('SignName', sms_sign)
        com_request.add_query_param('TemplateCode', template_id)
        param_data = {
            'username': self.env.user.name,
            'message': self.message
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
                return {"state": False, 'msg': "发送消息失败!,Error:{}".format(cli_res['Message'])}
        except Exception as e:
            return {"state": False, 'msg': "发送消息失败,Error:{}".format(str(e))}

    @api.model
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





