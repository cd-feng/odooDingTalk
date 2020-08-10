# -*- coding: utf-8 -*-
import json
import threading
import time
from odoo import http, api
from odoo.http import request
from .crypto import DingTalkCrypto as dtc
import logging
_logger = logging.getLogger(__name__)

OARESULT = {
    'agree': '同意',
    'refuse': '拒绝',
    'redirect': '转交',
}


class DingTalkCallBackManage(http.Controller):

    @http.route('/web/dingtalk/mc/callback/do', type='json', auth='public', methods=['POST'], csrf=False)
    def web_dingtalk_callback_controller(self, **kw):
        """
        回调函数入口--当收到钉钉的回调请求时，需要解密内容，然后根据回调类型做不同的处理
        :param kw:
        :return:
        """
        json_str = request.jsonrequest
        _logger.info(json_str)
        callbacks = request.env['dingtalk.callback.manage'].sudo().search([])
        encrypt_result = False      # 解密后类型
        corp_id = False             # 钉钉企业的corp_id
        callback = False            # callback
        now_company = False         # 正在回调的公司
        for call in callbacks:
            # 遍历所有配置了多公司参数的公司配置
            config = request.env['dingtalk.mc.config'].sudo().search([('company_id', '=', call.company_id.id)], limit=1)
            if not config:
                continue
            try:
                # 因无法确定是哪一个企业发起的回调。所以在此将每个企业的id用于解密，解密无异常就表示该企业发生了回调操作并记录下改企业对象
                encrypt_result = self.encrypt_result(json_str.get('encrypt'), call.aes_key, config.corp_id)
                callback = call
                corp_id = config.corp_id
                now_company = call.company_id
                break
            except Exception:
                continue
        if not encrypt_result or not corp_id or not callback:
            return False
        logging.info(">>>encrypt_result:{}".format(encrypt_result))
        result_msg = json.loads(encrypt_result)   # 消息内容
        event_type = result_msg.get('EventType')  # 消息类型
        # 创建回调日志
        self.create_callback_log(event_type, result_msg, now_company)
        # 根据回调类型进行判断，做不同的类型处理
        # --------通讯录------
        if event_type in ['user_add_org', 'user_modify_org', 'user_leave_org']:
            employee = request.env['hr.employee']
            t = threading.Thread(target=employee.process_dingtalk_chat, args=(result_msg, now_company))
            t.start()
        # --------部门------
        elif event_type in ['org_dept_create', 'org_dept_modify', 'org_dept_remove']:
            employee = request.env['hr.department']
            t = threading.Thread(target=employee.process_dingtalk_chat, args=(result_msg, now_company))
            t.start()
        # -----审批事件--------
        elif event_type in ['bpms_task_change']:
            self.approval_task_change(result_msg, now_company)
        elif event_type in ['bpms_instance_change']:
            self.approval_instance_change(result_msg, now_company)
        # -----用户签到-----------
        elif event_type in ['check_in']:
            signs = request.env['dingtalk.signs.list']
            t = threading.Thread(target=signs.process_dingtalk_chat, args=(result_msg.get('StaffId'), result_msg.get('TimeStamp'), now_company))
            t.start()
        # -------群会话事件----------
        elif event_type in ['chat_add_member', 'chat_remove_member', 'chat_quit', 'chat_update_owner', 'chat_update_title', 'chat_disband']:
            chat = request.env['dingtalk.mc.chat']
            t = threading.Thread(target=chat.process_dingtalk_chat, args=(result_msg, now_company))
            t.start()
        # ------考勤事件------------
        elif event_type in ['attendance_check_record', 'attendance_schedule_change', 'attendance_overtime_duration']:
            attendance_env = request.env['hr.attendance.result']
            t = threading.Thread(target=attendance_env.process_dingtalk_chat, args=(result_msg, now_company))
            t.start()
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

    def approval_instance_change(self, msg, company):
        """
        钉钉回调-审批实例开始/结束方法函数，用于支持审批结束时调用对应模型执行的自定义结束函数
        :param msg:
        :param company:
        :return:
        """
        company_id = company.id
        domain = [('process_code', '=', msg.get('processCode')), ('company_id', '=', company_id)]
        temp = request.env['dingtalk.approval.template'].sudo().search(domain, limit=1)
        if temp:
            contract_domain = [('template_id', '=', temp.id), ('company_id', '=', company_id)]
            approval = request.env['dingtalk.approval.control'].sudo().search(contract_domain)
            if approval:
                oa_domain = [('dd_process_instance', '=', msg.get('processInstanceId')), ('company_id', '=', company_id)]
                oa_model = request.env[approval.oa_model_id.model].sudo().search(oa_domain, limit=1)
                if oa_model:
                    approval_result = msg.get('result')
                    model_name = oa_model._name.replace('.', '_')
                    # 审批实例开始
                    if msg.get('type') == 'start':
                        oa_model.message_post(body="流程审批开始", message_type='notification')
                    # 审批实例结束
                    else:
                        sql = """UPDATE {} 
                            SET 
                                dd_approval_state='stop', 
                                dd_doc_state='审批结束', 
                                dd_approval_result='{}' 
                            WHERE 
                                id={}
                        """.format(model_name, approval_result, oa_model.id)
                        request.env.cr.execute(sql)
                        oa_model.message_post(body="流程审批结束", message_type='notification')
                        # -----检查审批结果，并执行审批通过或拒绝的自定义函数------
                        # 审批结果：同意
                        if approval_result == 'agree' and approval.approval_pass_function:
                            for method in approval.approval_pass_function.split(','):
                                try:
                                    getattr(oa_model, method)()
                                except Exception as e:
                                    self.print_getattr_exception(oa_model._name, e)
                        # 审批结果：拒绝
                        if approval_result == 'refuse' and approval.approval_refuse_function:
                            for method in approval.approval_refuse_function.split(','):
                                try:
                                    getattr(oa_model, method)()
                                except Exception as e:
                                    self.print_getattr_exception(oa_model._name, e)
        return True

    def approval_task_change(self, msg, company):
        """
        钉钉回调-审批任务开始/结束/转交
        :param msg:
        :param company:
        :return:
        """
        company_id = company.id
        domain = [('process_code', '=', msg.get('processCode')), ('company_id', '=', company_id)]
        temp = request.env['dingtalk.approval.template'].sudo().search(domain, limit=1)
        if temp:
            contract_domain = [('template_id', '=', temp.id), ('company_id', '=', company_id)]
            approval = request.env['dingtalk.approval.control'].sudo().search(contract_domain)
            if approval:
                pi = msg.get('processInstanceId')  # 审批实例ID
                msg_type = msg.get('type')  # 类型
                msg_result = msg.get('result')  # 审批结果
                ac = ''  # 审批消息内容
                oa_domain = [('dd_process_instance', '=', pi), ('company_id', '=', company_id)]
                oa_model = request.env[approval.oa_model_id.model].sudo().search(oa_domain)
                emp = request.env['hr.employee'].sudo().search([('ding_id', '=', msg.get('staffId')), ('company_id', '=', company_id)])
                model_name = oa_model._name.replace('.', '_')
                if msg_type == 'start' and oa_model:
                    ac = "等待({})审批".format(emp.name if emp else '')
                    if oa_model.sudo().dd_approval_state != 'stop':
                        request.env.cr.execute("UPDATE {} SET dd_doc_state='{}' WHERE id={}".format(model_name, ac, oa_model[0].id))
                    oa_model.message_post(body=ac, message_type='notification')
                elif msg_type == 'comment' and oa_model:
                    dobys = "{}评论了单据：{}".format(emp.name, msg.get('content'))
                    oa_model.message_post(body=dobys, message_type='notification')
                    ac = msg.get('content')
                elif msg_type == 'finish' and oa_model:
                    ac = msg.get('remark')
                    dobys = "{}：审批结果：{}，审批意见:{}".format(emp.name, OARESULT.get(msg_result), ac)
                    oa_model.message_post(body=dobys, message_type='notification')
                # 创建审批记录
                self.create_approval_record(approval.oa_model_id.id, oa_model.id, pi, emp.id, msg_type, msg_result, ac, company_id)

    def create_approval_record(self, model_id, rec_id, pi, emp_id, at, ar, ac, company_id):
        """
        创建审批记录
        :param model_id:  模型
        :param rec_id:    记录ID
        :param pi: 审批实例ID
        :param emp_id: 操作人
        :param at: 类型
        :param ar: 审批结果
        :param ac: 内容
        :param company_id: 公司
        :return:
        """
        record = request.env['dingtalk.approval.record']
        t = threading.Thread(target=record.process_dingtalk_chat, args=(model_id, rec_id, pi, emp_id, at, ar, ac, company_id))
        t.start()
        return True

    def print_getattr_exception(self, model_name, e):
        """
        :param model_name:
        :param e:
        :return:
        """
        _logger.info("----执行模型{}自定义结束函数失败-----".format(model_name))
        _logger.info(e)
        _logger.info("---------------------------------")

    def create_callback_log(self, event_type, result_msg, company):
        """
        创建回调日志
        :return:
        """
        log = request.env['dingtalk.callback.log']
        t = threading.Thread(target=log.process_dingtalk_chat, args=(event_type, result_msg, company))
        t.start()
        return True
