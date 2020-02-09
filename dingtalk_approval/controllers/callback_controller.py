# -*- coding: utf-8 -*-

from odoo.addons.dingtalk_callback.controllers.callback_controller import DingTalkCallBackManage
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

OARESULT = {
    'agree': '同意',
    'refuse': '拒绝',
    'redirect': '转交',
}


class DingTalkCallBackManageExt(DingTalkCallBackManage):

    def bpms_task_change(self, msg):
        """
        钉钉回调-审批任务开始/结束/转交
        :param msg:

        :return:
        """
        temp = request.env['dingtalk.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))], limit=1)
        if temp:
            approval = request.env['dingtalk.approval.control'].sudo().search([('template_id', '=', temp.id)])
            if approval:
                oa_model = request.env[approval.oa_model_id.model].sudo().search([('dd_process_instance', '=', msg.get('processInstanceId'))])
                emp = request.env['hr.employee'].sudo().search([('ding_id', '=', msg.get('staffId'))])
                model_name = oa_model._name.replace('.', '_')
                if msg.get('type') == 'start' and oa_model:
                    doc_text = "等待({})审批".format(emp.name if emp else '')
                    if oa_model.sudo().dd_approval_state != 'stop':
                        request.env.cr.execute(
                            "UPDATE {} SET dd_doc_state='{}' WHERE id={}".format(model_name, doc_text, oa_model[0].id))
                    oa_model.message_post(body=doc_text, message_type='notification')
                elif msg.get('type') == 'comment' and oa_model:
                    dobys = "{}评论了单据：{}".format(emp.name, msg.get('content'))
                    oa_model.message_post(body=dobys, message_type='notification')
                elif msg.get('type') == 'finish' and oa_model:
                    dobys = "{}：审批结果：{}，审批意见:{}".format(emp.name, OARESULT.get(msg.get('result')), msg.get('remark'))
                    oa_model.message_post(body=dobys, message_type='notification')
        return True

    def bpms_instance_change(self, msg):
        """
        钉钉回调-审批实例开始/结束方法函数，用于支持审批结束时调用对应模型执行的自定义结束函数
        :param msg:
        :return:
        """
        temp = request.env['dingtalk.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))], limit=1)
        if temp:
            approval = request.env['dingtalk.approval.control'].sudo().search([('template_id', '=', temp.id)])
            if approval:
                oa_model = request.env[approval.oa_model_id.model].sudo().search([('dd_process_instance', '=', msg.get('processInstanceId'))], limit=1)
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

    def print_getattr_exception(self, model_name, e):
        """
        :param model_name:
        :param e:
        :return:
        """
        _logger.info("----执行模型{}自定义结束函数失败-----".format(model_name))
        _logger.info(e)
        _logger.info("---------------------------------")