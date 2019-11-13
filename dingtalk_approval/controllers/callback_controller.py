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
        temp = request.env['dingtalk.approval.template'].sudo().search([('process_code', '=', msg.get('processCode'))])
        if temp:
            approval = request.env['dingtalk.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
            if approval:
                oa_model = request.env[approval.oa_model_id.model].sudo().search([('dd_process_instance', '=', msg.get('processInstanceId'))])
                if oa_model:
                    model_name = oa_model._name.replace('.', '_')
                    if msg.get('type') == 'start':
                        oa_model.sudo().message_post(body="流程审批开始", message_type='notification')
                    else:
                        request.env.cr.execute("""
                                    UPDATE {} SET 
                                        dd_approval_state='stop', 
                                        dd_doc_state='审批结束',
                                        dd_approval_result='{}' 
                                    WHERE id={}""".format(model_name, msg.get('result'), oa_model[0].id))
                        dobys = "流程审批结束"
                        oa_model.sudo().message_post(body=dobys, message_type='notification')
                        # -----执行自定义结束函数-----
                        if approval.approval_end_function:
                            for method in approval.approval_end_function.split(','):
                                try:
                                    getattr(oa_model, method)()
                                except Exception as e:
                                    _logger.info("----执行模型{}自定义结束函数失败-----".format(oa_model._name))
                                    _logger.info(e)
                                    _logger.info("---------------------------------")
        return True
