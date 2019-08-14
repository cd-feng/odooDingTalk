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
import time
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
from odoo.http import request
from .crypto import DingTalkCrypto as dtc

_logger = logging.getLogger(__name__)

OARESULT = {
    'agree': '同意',
    'refuse': '拒绝',
    'redirect': '转交',
}


class CallBack(Home, http.Controller):

    # 钉钉回调
    @http.route('/dingding/callback/eventreceive', type='json', auth='none', methods=['POST'], csrf=False)
    def dingding_callback_controller(self, **kw):
        logging.info(">>>钉钉回调事件")
        json_str = request.jsonrequest
        call_back, din_corpId = self.get_bash_attr()
        msg = self.encrypt_result(json_str.get('encrypt'), call_back.aes_key, din_corpId)
        logging.info(">>>解密消息结果:{}".format(msg))
        msg = json.loads(msg)
        event_type = msg.get('EventType')
        # --------通讯录------
        # if event_type == 'user_add_org' or event_type == 'user_modify_org' or event_type == 'user_leave_org':
        #     if event_type == 'user_leave_org':
        #         UserId = msg.get('UserId')
        #         for user_id in UserId:
        #             emp = request.env['hr.employee'].sudo().search([('din_id', '=', user_id)])
        #             emp.sudo().write({'active': False})
        #     else:
        #         request.env['dingding.bash.data.synchronous'].sudo().synchronous_dingding_employee()
        # elif event_type == 'org_dept_create' or event_type == 'org_dept_modify' or event_type == 'org_dept_remove':
        #     DeptId = msg.get('DeptId')
        #     if event_type == 'org_dept_remove':
        #         for dept in DeptId:
        #             hr_depat = request.env['hr.department'].sudo().search([('din_id', '=', dept)])
        #             if hr_depat:
        #                 hr_depat.sudo().unlink()
        #     else:
        #         request.env['dingding.bash.data.synchronous'].sudo().synchronous_dingding_department()
        # # -----员工角色-------
        # elif event_type == 'label_user_change' or event_type == 'label_conf_add' or event_type == 'label_conf_del' \
        #         or event_type == 'label_conf_modify':
        #     logging.info(">>>钉钉回调-员工角色信息发生变更/增加/删除/修改")
        # # -----审批-----------
        # elif event_type == 'bpms_task_change':
        #     self.bpms_task_change(msg)
        # elif event_type == 'bpms_instance_change':
        #     self.bpms_instance_change(msg)
        # # -----用户签到-----------
        # elif event_type == 'check_in':
        #     request.env['dindin.signs.list'].sudo().get_signs_by_user(msg.get('StaffId'), msg.get('TimeStamp'))
        # # -------群会话事件----------
        # elif event_type == 'chat_add_member' or event_type == 'chat_remove_member' or event_type == 'chat_quit' or \
        #         event_type == 'chat_update_owner' or event_type == 'chat_update_title' or event_type == 'chat_disband':
        #     request.env['dingding.chat'].sudo().process_dingding_chat_onchange(msg)
        # 返回加密结果
        return self.result_success(call_back.aes_key, call_back.token, din_corpId)

    def result_success(self, encode_aes_key, token, din_corpid):
        """
        封装success返回值
        :param encode_aes_key:
        :param token:
        :param din_corpid:
        :return:
        """
        dc = dtc(encode_aes_key, din_corpid)
        # 加密数据
        encrypt = dc.encrypt('success')
        timestamp = str(int(round(time.time())))
        nonce = dc.generateRandomKey(8)
        # 生成签名
        signature = dc.generateSignature(nonce, timestamp, token, encrypt)
        new_data = {
            'json': True,
            'data': {
                'msg_signature': signature,
                'timeStamp': timestamp,
                'nonce': nonce,
                'encrypt': encrypt
            }
        }
        return new_data

    def encrypt_result(self, encrypt, encode_aes_key, din_corpid):
        """
        解密钉钉回调返回的值
        :param encrypt:
        :param encode_aes_key:
        :param din_corpid:
        :return: json-string
        """
        dc = dtc(encode_aes_key, din_corpid)
        return dc.decrypt(encrypt)

    def get_bash_attr(self):
        """
        返回钉钉回调管理中的对象
        :return:
        """
        call_back = request.env['dingding.callback.manage'].sudo().search([], limit=1)
        if not call_back:
            raise UserError("钉钉回调管理单据错误，无法获取token和encode_aes_key值!")
        corp_id = request.env['ir.config_parameter'].sudo().get_param('dingding_base.corp_id')
        if not corp_id:
            raise UserError("钉钉CorpId值为空，请前往设置中进行配置!")
        return call_back, corp_id

    def bpms_instance_change(self, msg):
        """
        钉钉回调-钉钉回调-审批实例开始/结束
        :param msg:
        :return:
        """
        dn = datetime.datetime.now()
        temp = request.env['dindin.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))])
        if temp:
            appro = request.env['dindin.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
            if appro:
                oa_model = request.env[appro.oa_model_id.model].sudo().search(
                    [('process_instance_id', '=', msg.get('processInstanceId'))])
                if oa_model:
                    if msg.get('type') == 'start':
                        dobys = "审批流程开始-时间:{}".format(dn.strftime('%Y/%m/%d %H:%M:%S'))
                        oa_model.sudo().message_post(body=dobys, message_type='notification')
                    else:
                        oa_model.sudo().write({'oa_state': '02', 'oa_message': "审批结束", 'oa_result': msg.get('result')})
                        dobys = "审批流程结束-时间:{}".format(dn.strftime('%Y/%m/%d %H:%M:%S'))
                        oa_model.sudo().message_post(body=dobys, message_type='notification')
        return True

    def bpms_task_change(self, msg):
        """
        钉钉回调-审批任务开始/结束/转交
        :param msg:
        :return:
        """
        dn = datetime.datetime.now()
        temp = request.env['dindin.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))])
        if temp:
            appro = request.env['dindin.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
            if appro:
                oa_model = request.env[appro.oa_model_id.model].sudo().search(
                    [('process_instance_id', '=', msg.get('processInstanceId'))])
                emp = request.env['hr.employee'].sudo().search([('din_id', '=', msg.get('staffId'))])
                if msg.get('type') == 'start' and oa_model:
                    if oa_model.sudo().oa_state != '02':
                        oa_model.sudo().write({'oa_message': "等待{}审批".format(emp.name if emp else '')})
                    dobys = "{}: 等待{}审批".format(dn.strftime('%Y-%m-%d %H:%M:%S'), emp.name)
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
                elif msg.get('type') == 'comment' and oa_model:
                    dobys = "{}: (评论消息)-评论人:{}; 评论内容:{}".format(dn.strftime('%Y-%m-%d %H:%M:%S'), emp.name,
                                                               msg.get('content'))
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
                elif msg.get('type') == 'finish' and oa_model:
                    dobys = "{}: {}已审批; 审批结果:{}; 审批意见:{}".format(dn.strftime('%Y-%m-%d %H:%M:%S'), emp.name,
                                                                       OARESULT.get(msg.get('result')),
                                                                       msg.get('remark'))
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
        return True

