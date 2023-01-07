# -*- coding: utf-8 -*-

import logging
from odoo import http, _, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.dataset import DataSet
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DingTalkDataSet(DataSet):

    @http.route('/web/dataset/call_button', type='json', auth="user")
    def call_button(self, model, method, args, kwargs):
        # 获取当前操作的单据
        try:
            if args[0]:
                res_id = args[0][0]
            else:
                params = args[1].get('params')
                res_id = params.get('id')
            now_model = request.env[model].sudo().search([('id', '=', res_id)], limit=1)
        except Exception:
            return super(DingTalkDataSet, self).call_button(model, method, args, kwargs)
        # 尝试获取公司id
        try:
            company_id = now_model.company_id.id
        except Exception:
            uid = kwargs.get('context').get('uid')
            user = request.env['res.users'].with_user(SUPERUSER_ID).search([('id', '=', uid)], limit=1)
            company_id = user.company_id.id
        ir_model = request.env['ir.model'].with_user(SUPERUSER_ID).search([('model', '=', model)], limit=1)
        domain = [('oa_model_id', '=', ir_model.id), ('company_id', '=', company_id), ('state', '=', 'open')]
        approval_controls = request.env['dingtalk.approval.control'].with_user(SUPERUSER_ID).search(domain)
        if approval_controls:
            approval = None
            if len(approval_controls) == 1:
                approval = approval_controls[0]
            else:
                for approval_obj in approval_controls:
                    if approval_obj.model_field_id and now_model[approval_obj.model_field_id.name] == approval_obj.model_field_value:
                        approval = approval_obj
                        break
            # 检查是否读取到了审批配置
            if approval:
                if now_model.dd_approval_state == 'draft':
                    start_but_functions = list()
                    for button in approval.model_start_button_ids:
                        start_but_functions.append(button.function)
                    if method in start_but_functions:
                        raise ValidationError(_("本功能暂无法使用，因为单据还没有'提交至钉钉'进行审批，请先提交至钉钉进行审批后再试！"))
                elif now_model.dd_approval_state == 'approval':
                    but_functions = list()
                    for button in approval.model_button_ids:
                        but_functions.append(button.function)
                    if method in but_functions:
                        raise ValidationError(_("本功能暂无法使用，因为单据还是'钉钉审批中'状态。请在单据审批后再试！"))
                elif now_model.dd_approval_result == 'agree':
                    pass_but_functions = list()
                    for button in approval.model_pass_button_ids:
                        pass_but_functions.append(button.function)
                    if method in pass_but_functions:
                        raise ValidationError(_("本功能暂无法使用，因为单据已经配置了'审批通过后'不允许使用本功能。"))
                elif now_model.dd_approval_result == 'refuse':
                    end_but_functions = list()
                    for button in approval.model_end_button_ids:
                        end_but_functions.append(button.function)
                    if method in end_but_functions:
                        raise ValidationError(_("本功能暂无法使用，因为单据已经配置了'审批拒绝后'不允许使用本功能。"))
                elif now_model.dd_approval_result == 'terminate':
                    start_but_functions = list()
                    for button in approval.model_start_button_ids:
                        start_but_functions.append(button.function)
                    if method in start_but_functions:
                        raise ValidationError(_("本功能暂无法使用，因为单据还没有'提交至钉钉'进行审批，请先提交至钉钉进行审批后再试！"))
        return super(DingTalkDataSet, self).call_button(model, method, args, kwargs)
