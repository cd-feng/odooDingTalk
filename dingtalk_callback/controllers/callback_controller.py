# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import json
import time
from odoo import http
from odoo.http import request
from .crypto import DingTalkCrypto as dtc
import logging
from odoo.addons.dingtalk_base.tools import dingtalk_api
_logger = logging.getLogger(__name__)


class DingTalkCallBackManage(http.Controller):

    @http.route('/web/dingtalk/callback/do', type='json', auth='public', methods=['POST'], csrf=False)
    def web_dingtalk_callback_controller(self, **kw):
        json_str = request.jsonrequest
        callback = request.env['dingtalk.callback.manage'].sudo().search([], limit=1)
        if not callback:
            return False
        corp_id = dingtalk_api.get_dt_corp_id()
        encrypt_result = self.encrypt_result(json_str.get('encrypt'), callback.aes_key, corp_id)
        logging.info(">>>encrypt_result:{}".format(encrypt_result))
        result_msg = json.loads(encrypt_result)
        event_type = result_msg.get('EventType')
        # --------通讯录------
        if event_type == 'user_add_org' or event_type == 'user_modify_org' or event_type == 'user_leave_org':
            user_ids = result_msg.get('UserId')
            if event_type == 'user_leave_org':
                # 用户离职
                employees = request.env['hr.employee'].sudo().search([('ding_id', 'in', user_ids)])
                if employees:
                    employees.sudo().write({'active': False})
            else:
                # 用户增加和变更时获取该用户详情
                for user_id in user_ids:
                    self.get_employee_info(user_id, event_type)
        # --------部门------
        elif event_type == 'org_dept_create' or event_type == 'org_dept_modify' or event_type == 'org_dept_remove':
            dept_ids = result_msg.get('DeptId')
            if event_type == 'org_dept_remove':
                departments = request.env['hr.department'].sudo().search([('ding_id', 'in', dept_ids)])
                if departments:
                    departments.sudo().write({'active': False})
            else:
                # 部门增加和变更时获取该部门详情
                for dept_id in dept_ids:
                    self.get_department_info(dept_id, event_type)
        # # -----审批-----------
        elif event_type == 'bpms_task_change':
            self.bpms_task_change(result_msg)
        elif event_type == 'bpms_instance_change':
            self.bpms_instance_change(result_msg)
        # -----用户签到-----------
        elif event_type == 'check_in':
            self.user_check_in(result_msg.get('StaffId'), result_msg.get('TimeStamp'))
        # -------群会话事件----------
        elif event_type == 'chat_add_member' or event_type == 'chat_remove_member' or event_type == 'chat_quit' or \
                event_type == 'chat_update_owner' or event_type == 'chat_update_title' or event_type == 'chat_disband':
        #     request.env['dingding.chat'].sudo().process_dingding_chat_onchange(result_msg)
            self.chat_info_onchange(result_msg)
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

    def bpms_instance_change(self, msg):
        """
        钉钉回调-钉钉回调-审批实例开始/结束
        :param msg:
        :return:
        """
        pass

    def bpms_task_change(self, msg):
        """
        钉钉回调-审批任务开始/结束/转交
        :param msg:

        :return:
        """
        pass

    def get_employee_info(self, user_id, event_type):
        try:
            result = dingtalk_api.get_client().user.get(user_id)
        except Exception as e:
            _logger.info("获取用户详情失败：{}".format(e))
            return
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
                'ding_avatar_url': result.get('avatar') if result.get('avatar') else '',  # 钉钉头像url
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
                date_str = dingtalk_api.timestamp_to_local_date(result.get('hiredDate'))
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
        try:
            result = dingtalk_api.get_client().department.get(dept_id)
        except Exception as e:
            _logger.info("获取用户详情失败：{}".format(e))
            return
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
            else:
                data['is_root'] = True
            depts = result.get('deptManagerUseridList').split("|")
            manage_users = request.env['hr.employee'].sudo().search([('ding_id', 'in', depts)])
            data.update({
                'manager_user_ids': [(6, 0, manage_users.ids)],
                'manager_id': manage_users[0].id
            })
            if event_type == 'org_dept_create':
                request.env['hr.department'].sudo().create(data)
            elif event_type == 'org_dept_modify':
                domain = [('ding_id', '=', result.get('id'))]
                h_department = request.env['hr.department'].sudo().search(domain)
                if h_department:
                    h_department.sudo().write(data)
        return True

    def user_check_in(self, userid, signtime):
        """
        用户签到-事件
        :param userid:
        :param signtime:
        :return:
        """
        pass

    def chat_info_onchange(self, result_msg):
        """
        群会话事件
        :param result_msg:
        :return:
        """
        pass
