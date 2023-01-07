# -*- coding: utf-8 -*-
from odoo import models, fields, SUPERUSER_ID, api
import logging
_logger = logging.getLogger(__name__)

OARESULT = {'agree': '同意', 'refuse': '拒绝', 'redirect': '转交'}


class Dingtalk2Callbacks(models.AbstractModel):
    _inherit = 'dingtalk2.callbacks'

    @api.model
    def deal_dingtalk_msg(self, event_type, encrypt_result, res_company):
        """
        处理回调的消息
        :param event_type     钉钉回调类型
        :param encrypt_result 钉钉回调的消息内容
        :param res_company    回调的公司
        """
        company_id = res_company.id
        if event_type in ['bpms_task_change', 'bpms_instance_change']:
            domain = [('process_code', '=', encrypt_result.get('processCode')), ('company_id', '=', company_id)]
            approval_template = self.env['dingtalk.approval.template'].sudo().search(domain, limit=1)
            if event_type == 'bpms_task_change':  # 审批任务开始、结束、转交。
                return self._approval_task_change(encrypt_result, company_id, approval_template.id)
            elif event_type == 'bpms_instance_change':   # 审批实例开始、结束。
                return self._approval_instance_change(encrypt_result, company_id, approval_template.id)
        return super(Dingtalk2Callbacks, self).deal_dingtalk_msg(event_type, encrypt_result, res_company)

    def _approval_instance_change(self, encrypt_result, company_id, template_id):
        """
        钉钉回调-审批实例开始/结束方法函数，用于支持审批结束时调用对应模型执行的自定义结束函数
        :param encrypt_result:
        :param company_id:
        :return:
        """
        contract_domain = [('template_id', '=', template_id), ('company_id', '=', company_id)]
        approval = self.env['dingtalk.approval.control'].with_user(SUPERUSER_ID).search(contract_domain)
        if approval:
            model_obj = self.env[approval.oa_model_id.model]
            process_instance = encrypt_result.get('processInstanceId')
            try:
                model_obj.company_id
                oa_domain = [('dd_process_instance', '=', process_instance), ('company_id', '=', company_id)]
            except Exception:
                oa_domain = [('dd_process_instance', '=', process_instance)]
            oa_model = model_obj.with_user(SUPERUSER_ID).search(oa_domain, limit=1)
            if oa_model:
                approval_result = encrypt_result.get('result')
                model_name = oa_model._name.replace('.', '_')
                # 审批实例开始
                if encrypt_result.get('type') == 'start':
                    try:
                        oa_model.message_post(body="流程审批开始", message_type='notification')
                    except Exception as e:
                        _logger.info(str(e))
                    return self._create_approval_log(oa_model, process_instance, "审批实例开始", company_id)
                # 撤销实例
                elif encrypt_result.get('type') == 'terminate':
                    sql = """UPDATE {} SET dd_approval_state='stop', dd_doc_state='申请被撤销', dd_approval_result='terminate'
                             WHERE id={}""".format(model_name, oa_model.id)
                    self._cr.execute(sql)
                    try:
                        oa_model.message_post(body="单据已被撤销", message_type='notification')
                    except Exception as e:
                        _logger.info(str(e))
                    # oa_model.create_uid.notify_warning(title="钉钉工作流", message="您提交的{}已被撤销，请及时查看！".
                    #                                    format(approval.oa_model_id.name), sticky=True)
                    return self._create_approval_log(oa_model, process_instance, "审批实例已被撤销", company_id)
                # 审批实例结束
                else:
                    sql = """UPDATE {} SET dd_approval_state='stop', dd_doc_state='审批结束', dd_approval_result='{}'
                        WHERE id={}""".format(model_name, approval_result, oa_model.id)
                    self._cr.execute(sql)
                    try:
                        oa_model.message_post(body="流程审批结束", message_type='notification')
                    except Exception as e:
                        _logger.info(str(e))
                    # -----检查审批结果，并执行审批通过或拒绝的自定义函数------
                    # 审批结果：同意
                    if approval_result == 'agree' and approval.approval_pass_function:
                        for method in approval.approval_pass_function.split(','):
                            try:
                                getattr(oa_model, method)()
                            except Exception as e:
                                _logger.info(">模型{}自定义结束函数失败:{}".format(model_name, str(e)))
                    # 审批结果：拒绝
                    if approval_result == 'refuse' and approval.approval_refuse_function:
                        for method in approval.approval_refuse_function.split(','):
                            try:
                                getattr(oa_model, method)()
                            except Exception as e:
                                _logger.info(">模型{}自定义结束函数失败:{}".format(model_name, str(e)))
                    # oa_model.create_uid.notify_info(title="钉钉工作流", message="您提交的{}已审批结束！".
                    #                                 format(approval.oa_model_id.name), sticky=True)
                    return self._create_approval_log(oa_model, process_instance, "审批实例结束", company_id)

    def _approval_task_change(self, encrypt_result, company_id, template_id):
        """
        钉钉回调-审批任务开始/结束/转交
        :param encrypt_result:
        :param company_id:
        :param template_id:
        :return:
        """
        contract_domain = [('template_id', '=', template_id), ('company_id', '=', company_id)]
        approval = self.env['dingtalk.approval.control'].with_user(SUPERUSER_ID).search(contract_domain)
        if approval:
            process_instance = encrypt_result.get('processInstanceId')  # 审批实例ID
            msg_type = encrypt_result.get('type')      # 类型
            msg_result = encrypt_result.get('result')  # 审批结果
            oa_model_obj = self.env[approval.oa_model_id.model]
            try:
                oa_model_obj.company_id
                oa_domain = [('dd_process_instance', '=', process_instance), ('company_id', '=', company_id)]
            except Exception:
                oa_domain = [('dd_process_instance', '=', process_instance)]
            oa_model = oa_model_obj.with_user(SUPERUSER_ID).search(oa_domain)
            emp = self.env['hr.employee'].with_user(SUPERUSER_ID).search(
                [('ding_id', '=', encrypt_result.get('staffId')), ('company_id', '=', company_id)])
            model_name = oa_model._name.replace('.', '_')
            if msg_type == 'start' and oa_model:
                dobys = "等待[{}]审批".format(emp.name if emp else '')
                if oa_model.with_user(SUPERUSER_ID).dd_approval_state != 'stop':
                    self._cr.execute(
                        "UPDATE {} SET dd_doc_state='{}' WHERE id={}".format(model_name, dobys, oa_model[0].id))
                try:
                    oa_model.message_post(body=dobys, message_type='notification')
                except Exception as e:
                    _logger.error(str(e))
                # oa_model.create_uid.notify_default(title="钉钉审批消息", message=dobys, sticky=False)
                return self._create_approval_log(oa_model, process_instance, dobys, company_id, emp)
            elif msg_type == 'comment' and oa_model:
                dobys = "[{}]评论了你提交的单据：{}".format(emp.name, encrypt_result.get('content'))
                try:
                    oa_model.message_post(body=dobys, message_type='notification')
                except Exception as e:
                    _logger.error(str(e))
                # oa_model.create_uid.notify_default(title="钉钉审批消息", message=dobys, sticky=False)
                return self._create_approval_log(oa_model, process_instance, dobys, company_id, emp)
            elif msg_type == 'finish' and oa_model:
                dobys = "审批人：[{}]；审批结果：{}；审批意见:{}".format(emp.name, OARESULT.get(msg_result), encrypt_result.get('remark') or '无')
                try:
                    oa_model.message_post(body=dobys, message_type='notification')
                except Exception as e:
                    _logger.error(str(e))
                # oa_model.create_uid.notify_default(title="钉钉审批消息", message=dobys, sticky=False)
                return self._create_approval_log(oa_model, process_instance, dobys, company_id, emp)

    def _create_approval_log(self, res_model, process_instance, content, company_id, emp=None):
        """
        创建审批日志
        :return:
        """
        self.env['dingtalk.approval.log'].sudo().create({
            'res_model': res_model._name,
            'res_id': res_model.id,
            'process_instance': process_instance,
            'user_id': res_model.create_uid.id,
            'employee_id': emp.id if emp else False,
            'approval_content': content,
            'company_id': company_id,
        })
