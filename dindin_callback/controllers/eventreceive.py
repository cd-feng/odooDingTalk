# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time
import threading
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class CallBack(Home, http.Controller):

    # 钉钉回调
    @http.route('/callback/eventreceive', type='json', auth='none', methods=['POST'], csrf=False)
    def callback_users(self, **kw):
        logging.info(">>>钉钉回调事件")
        json_str = request.jsonrequest
        call_back, din_corpId = self.get_bash_attr()
        msg = self.encrypt_result(json_str.get('encrypt'), call_back.aes_key, din_corpId)
        logging.info(">>>解密消息结果:{}".format(msg))
        msg = json.loads(msg)
        event_type = msg.get('EventType')
        # -------------------
        # -----通讯录---------
        # -------------------
        if event_type == 'user_add_org' or event_type == 'user_modify_org' or event_type == 'user_leave_org':
            logging.info(">>>钉钉回调-用户增加、更改、离职")
            if event_type == 'user_leave_org':
                UserId = msg.get('UserId')
                for user_id in UserId:
                    emp = request.env['hr.employee'].sudo().search([('din_id', '=', user_id)])
                    if emp:
                        emp.sudo().unlink()
            else:
                request.env['dindin.synchronous.employee'].start_synchronous_employee()
        elif event_type == 'org_dept_create' or event_type == 'org_dept_modify' or event_type == 'org_dept_remove':
            logging.info(">>>钉钉回调-通讯录企业部门创建/修改/删除")
            DeptId = self.msg.get('DeptId')
            if event_type == 'org_dept_remove':
                for dept in DeptId:
                    hr_depat = request.env['hr.department'].sudo().search([('din_id', '=', dept)])
                    if hr_depat:
                        hr_depat.sudo().unlink()
            else:
                request.env['dindin.synchronous.department'].start_synchronous_department()
        # -------------------
        # -----员工角色-------
        # -------------------
        elif event_type == 'label_user_change' or event_type == 'label_conf_add' or event_type == 'label_conf_del' \
                or event_type == 'label_conf_modify':
            logging.info(">>>钉钉回调-员工角色信息发生变更/增加/删除/修改")
        # -------------------
        # -----审批-----------
        # -------------------
        elif event_type == 'bpms_task_change':
            logging.info(">>>钉钉回调-审批任务开始/结束/转交")
            self.bpms_task_change(msg)
        elif event_type == 'bpms_instance_change':
            logging.info(">>>钉钉回调-审批实例开始/结束")
            self.bpms_instance_change(msg)
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
        from .dingtalk.crypto import DingTalkCrypto as dtc
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
        from .dingtalk.crypto import DingTalkCrypto as dtc
        dc = dtc(encode_aes_key, din_corpid)
        return dc.decrypt(encrypt)

    def get_bash_attr(self):
        """
        :return:
        """
        call_back = request.env['dindin.users.callback'].sudo().search([])
        if not call_back:
            raise UserError("钉钉回调管理单据错误，无法获取token和encode_aes_key值!")
        din_corpId = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
        if not din_corpId:
            raise UserError("钉钉CorpId值为空，请前往设置中进行配置!")
        return call_back[0], din_corpId

    def bpms_instance_change(self, msg):
        """
        钉钉回调-钉钉回调-审批实例开始/结束
        :param msg:
        :return:
        """
        temp = request.env['dindin.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))])
        if temp:
            appro = request.env['dindin.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
            if appro:
                oa_model = self.env[appro.oa_model_id.model].sudo().search([('process_instance_id', '=', msg.get('processInstanceId'))])
                if msg.get('type') == 'start' and oa_model:
                    oa_model.sudo().write({'oa_state': '01'})
                else:
                    oa_model.sudo().write({'oa_state': '02'})
        return True

    def bpms_task_change(self, msg):
        """
        钉钉回调-审批任务开始/结束/转交
        :param msg:
        :return:
        """
        temp = request.env['dindin.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))])
        if temp:
            appro = request.env['dindin.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
            if appro:
                oa_model = self.env[appro.oa_model_id.model].sudo().search([('process_instance_id', '=', msg.get('processInstanceId'))])
                emp = self.env['hr.employee'].sudo().search([('din_id', '=', msg.get('staffId'))])
                if msg.get('type') == 'start' and oa_model:
                    oa_model.sudo().write({'oa_message': "审批人'{}'".format(emp.name if emp else '')})
                    dobys = "流程开始-时间:{} 审批人:{}".format(datetime.datetime.now(), emp.name)
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
                else:
                    dobys = "时间:{} 审批人:{} 意见为:{}".format(datetime.datetime.now(), emp.name, msg.get('remark'))
                    oa_model.sudo().message_post(body=dobys, message_type='notification')
                    oa_model.sudo().write({
                        'oa_message': "审批人'{}'".format(emp.name if emp else ''),
                        'oa_result': msg.get('result'),
                    })
        return True

# 钉钉回调-审批任务开始/结束/转交
# {"taskId":61056035232,"createTime":1554266952000,
# "staffId":"021038163631880229",
# "bizCategoryId":"",
# "EventType":"bpms_task_change",
# "type":"start","title":"燕春提交的Odoo请假单",
# "processCode":"PROC-EFYJFT8W-5KX30J3T41S0QC2H1TH32-S7SHPITJ-53",
# "processInstanceId":"e3f9c4c9-2fbf-4a0e-9098-40cb21e91d47","corpId":""}

# {"taskId":61056035232,"result":"agree","createTime":1554266952000,
# "staffId":"021038163631880229","remark":"","bizCategoryId":"",
# "EventType":"bpms_task_change","type":"finish","title":"燕春提交的Odoo请假单",
# "processCode":"PROC-EFYJFT8W-5KX30J3T41S0QC2H1TH32-S7SHPITJ-53",
# "processInstanceId":"e3f9c4c9-2fbf-4a0e-9098-40cb21e91d47","finishTime":1554267241000,"corpId":""}


# class DinDinThread(threading.Thread):
#     """
#     钉钉回调线程
#     """
#     encode_aes_key = None
#     token = None
#     din_corpid = None
#
#     def __init__(self, name, encode_aes_key, token, din_corpid):
#         threading.Thread.__init__(self)
#         self.name = name
#         self.encode_aes_key = encode_aes_key
#         self.token = token
#         self.din_corpid = din_corpid
#
#     def run(self):
#         logging.info(">>>开始线程:".format(self.name))
#         from .dingtalk.crypto import DingTalkCrypto as dtc
#         dc = dtc(self.encode_aes_key, self.din_corpid)
#         # 加密数据
#         encrypt = dc.encrypt('success')
#         timestamp = str(int(round(time.time())))
#         nonce = dc.generateRandomKey(8)
#         # 生成签名
#         signature = dc.generateSignature(nonce, timestamp, self.token, encrypt)
#         new_data = {
#             'json': True,
#             'data': {
#                 'msg_signature': signature,
#                 'timeStamp': timestamp,
#                 'nonce': nonce,
#                 'encrypt': encrypt
#             }
#         }
#         logging.info(">>>退出线程:".format(self.name))
#         return new_data
