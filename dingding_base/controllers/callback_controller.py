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
import time
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
from odoo.http import request
from .crypto import DingTalkCrypto as dtc
import logging
_logger = logging.getLogger(__name__)

OARESULT = {
    'agree': '同意',
    'refuse': '拒绝',
    'redirect': '转交',
}


class DingDingCallBackManage(Home, http.Controller):

    # 钉钉回调
    @http.route('/dingding/callback/eventreceive', type='json', auth='none', methods=['POST'], csrf=False)
    def dingding_callback_controller(self, **kw):
        json_str = request.jsonrequest
        callback, corp_id = self.get_bash_attr()
        msg = self.encrypt_result(json_str.get('encrypt'), callback.aes_key, corp_id)
        logging.info(">>>event_type:{}".format(msg))
        msg = json.loads(msg)
        event_type = msg.get('EventType')
        # --------通讯录------
        if event_type == 'user_add_org' or event_type == 'user_modify_org' or event_type == 'user_leave_org':
            if event_type == 'user_leave_org':   # 用户离职
                user_ids = msg.get('UserId')
                for user_id in user_ids:
                    emp = request.env['hr.employee'].sudo().search([('ding_id', '=', user_id)])
                    if emp:
                        emp.sudo().write({'active': False})
            else:  # 用户增加和变更时获取该用户详情
                user_ids = msg.get('UserId')
                for user_id in user_ids:
                    self.get_employee_info(user_id, event_type)
        # --------部门------
        elif event_type == 'org_dept_create' or event_type == 'org_dept_modify' or event_type == 'org_dept_remove':
            dept_ids = msg.get('DeptId')
            if event_type == 'org_dept_remove':
                for dept_id in dept_ids:
                    hr_depat = request.env['hr.department'].sudo().search([('ding_id', '=', dept_id)])
                    if hr_depat:
                        hr_depat.sudo().write({'active': False})
            else:  # 部门增加和变更时获取该部门详情
                for dept_id in dept_ids:
                    self.get_department_info(dept_id, event_type)
        # -----员工角色-------
        elif event_type == 'label_user_change' or event_type == 'label_conf_add' or event_type == 'label_conf_del' \
                or event_type == 'label_conf_modify':
            logging.info(">>>钉钉回调-员工角色信息发生变更/增加/删除/修改")
        # -----审批-----------
        elif event_type == 'bpms_task_change':
            self.bpms_task_change(msg)
        elif event_type == 'bpms_instance_change':
            self.bpms_instance_change(msg)
        # # -----用户签到-----------
        elif event_type == 'check_in':
            request.env['dingding.signs.list'].sudo().get_signs_by_user(msg.get('StaffId'), msg.get('TimeStamp'))
        # # -------群会话事件----------
        elif event_type == 'chat_add_member' or event_type == 'chat_remove_member' or event_type == 'chat_quit' or \
                event_type == 'chat_update_owner' or event_type == 'chat_update_title' or event_type == 'chat_disband':
            request.env['dingding.chat'].sudo().process_dingding_chat_onchange(msg)
        # 返回加密结果
        return self.result_success(callback.aes_key, callback.token, corp_id)

    def result_success(self, encode_aes_key, token, corp_id):
        """
        封装success返回值
        :param encode_aes_key:
        :param token:
        :param corp_id:
        :return:
        """
        dc = dtc(encode_aes_key, corp_id)
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
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        temp = request.env['dingding.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))])
        if temp:
            approval = request.env['dingding.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
            if approval:
                oa_model = request.env[approval.oa_model_id.model].sudo().search([('dd_process_instance', '=', msg.get('processInstanceId'))])
                if oa_model:
                    model_name = oa_model._name.replace('.', '_')
                    if msg.get('type') == 'start':
                        dobys = "审批流程开始-时间:{}".format(now_time)
                        # request.env.cr.execute("UPDATE {} SET dd_doc_state='审批流程开始' WHERE id={}".format(model_name, oa_model[0].id))
                        oa_model.sudo().message_post(body=dobys, message_type='notification')
                    else:
                        request.env.cr.execute("""
                            UPDATE {} SET 
                                dd_approval_state='stop', 
                                dd_doc_state='<span style="color:blue">审批结束</span>',
                                dd_approval_result='{}' 
                            WHERE id={}""".format(model_name, msg.get('result'), oa_model[0].id))
                        dobys = "审批流程结束-时间:{}".format(now_time)
                        oa_model.sudo().message_post(body=dobys, message_type='notification')
        return True

    def bpms_task_change(self, msg):
        """
        钉钉回调-审批任务开始/结束/转交
        :param msg:

        :return:
        """
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        temp = request.env['dingding.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))], limit=1)
        if temp:
            approval = request.env['dingding.approval.control'].sudo().search([('template_id', '=', temp.id)])
            if approval:
                oa_model = request.env[approval.oa_model_id.model].sudo().search([('dd_process_instance', '=', msg.get('processInstanceId'))])
                emp = request.env['hr.employee'].sudo().search([('ding_id', '=', msg.get('staffId'))])
                model_name = oa_model._name.replace('.', '_')
                if msg.get('type') == 'start' and oa_model:
                    if oa_model.sudo().dd_approval_state != 'stop':
                        doc_text = '待<span style="color:red">{}</span>审批'.format(emp.name if emp else '')
                        request.env.cr.execute(
                            "UPDATE {} SET dd_doc_state='{}' WHERE id={}".format(model_name, doc_text, oa_model[0].id))
                    dobys = "{}: 等待{}审批".format(now_time, emp.name)
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
                elif msg.get('type') == 'comment' and oa_model:
                    dobys = "{}: (评论消息)-评论人:{}; 评论内容:{}".format(now_time, emp.name, msg.get('content'))
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
                elif msg.get('type') == 'finish' and oa_model:
                    dobys = "{} {}：审批结果:{}，审批意见:{}".format(now_time, emp.name, OARESULT.get(msg.get('result')), msg.get('remark'))
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
        return True

    def get_employee_info(self, user_id, event_type):
        """
        从钉钉获取用户详情
        :param user_id:
        :param event_type:
        :return:
        """
        url, token = request.env['dingding.parameter'].sudo().get_parameter_value_and_token('user_get')
        data = {'userid': user_id}
        result = request.env['dingding.api.tools'].send_get_request(url, token, data, 15)
        if result.get('errcode') == 0:
            data = {
                'name': result.get('name'),  # 员工名称
                'ding_id': result.get('userid'),  # 钉钉用户Id
                'din_unionid': result.get('unionid'),  # 钉钉唯一标识
                'mobile_phone': result.get('mobile'),  # 手机号
                'work_phone': result.get('tel'),  # 分机号
                'work_location': result.get('workPlace'),  # 办公地址
                'notes': result.get('remark'),  # 备注
                'job_title': result.get('position'),  # 职位
                'work_email': result.get('email'),  # email
                'din_jobnumber': result.get('jobnumber'),  # 工号
                'din_avatar': result.get('avatar') if result.get('avatar') else '',  # 钉钉头像url
                'din_isSenior': result.get('isSenior'),  # 高管模式
                'din_isAdmin': result.get('isAdmin'),  # 是管理员
                'din_isBoss': result.get('isBoss'),  # 是老板
                'din_isHide': result.get('isHide'),  # 隐藏手机号
                'din_active': result.get('active'),  # 是否激活
                'din_isLeaderInDepts': result.get('isLeaderInDepts'),  # 是否为部门主管
                'din_orderInDepts': result.get('orderInDepts'),  # 所在部门序位
            }
            # 支持显示国际手机号
            if result.get('stateCode') != '86':
                data.update({
                    'mobile_phone': '+{}-{}'.format(result.get('stateCode'), result.get('mobile')),
                })
            if result.get('hiredDate'):
                date_str = request.env['dingding.api.tools'].get_time_stamp(result.get('hiredDate'))
                data.update({'din_hiredDate': date_str})
            if result.get('department'):
                dep_ding_ids = result.get('department')
                dep_list = request.env['hr.department'].sudo().search([('ding_id', 'in', dep_ding_ids)])
                data.update({'department_ids': [(6, 0, dep_list.ids)], 'department_id': dep_list[0].id if dep_list else False})
            if event_type == 'user_add_org':
                request.env['hr.employee'].sudo().create(data)
            else:
                employee = request.env['hr.employee'].sudo().search([('ding_id', '=', user_id)], limit=1)
                if employee:
                    employee.sudo().write(data)
        else:
            _logger.info("从钉钉同步员工时发生意外，原因为:{}".format(result.get('errmsg')))
        return True

    def get_department_info(self, dept_id, event_type):
        """
        获取部门详情
        :param dept_id:
        :param event_type:
        :return:
        """
        url, token = request.env['dingding.parameter'].sudo().get_parameter_value_and_token('department_get')
        data = {'id': dept_id}
        result = request.env['dingding.api.tools'].send_get_request(url, token, data, 15)
        if result.get('errcode') == 0:
            data = {
                'name': result.get('name'),
                'ding_id': result.get('id'),
            }
            if result.get('parentid') != 1:
                domain = [('ding_id', '=', result.get('parentid'))]
                partner_department = request.env['hr.department'].sudo().search(domain, limit=1)
                if partner_department:
                    data.update({'parent_id': partner_department.id})
            if event_type == 'org_dept_create':
                request.env['hr.department'].sudo().create(data)
            elif event_type == 'org_dept_modify':
                domain = [('ding_id', '=', result.get('id')), ('active', '=', True)]
                h_department = request.env['hr.department'].sudo().search(domain)
                if h_department:
                    h_department.sudo().write(data)
        return True


