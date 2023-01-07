# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api
from odoo.addons.base.models.ir_ui_view import Model


get_view_origin = Model.get_view


@api.model
def get_view(self, view_id=None, view_type='form', **options):
    result = get_view_origin(self, view_id, view_type, **options)
    view_get_approval_view(self, view_type, result)
    return result


Model.get_view = get_view


def modify_tree_view(obj, result):
    fields_info = obj.fields_get(allfields=['dd_doc_state', 'dd_approval_state', 'dd_approval_result'])
    arch = result.get('arch')
    tree = etree.fromstring(arch)
    if tree.tag != 'tree':
        return
    if 'dd_doc_state' in fields_info:
        field = etree.Element('field')
        field.set('name', 'dd_doc_state')
        field.set('widget', 'dd_approval_widget')
        tree.append(field)
    if 'dd_approval_state' in fields_info:
        field = etree.Element('field')
        field.set('name', 'dd_approval_state')
        field.set('widget', 'badge')
        field.set('optional', 'show')
        field.set('decoration-info', "dd_approval_state=='approval'")
        field.set('decoration-success', "dd_approval_state=='stop'")
        field.set('decoration-warning', "dd_approval_state=='draft'")
        tree.append(field)
    if 'dd_approval_result' in fields_info:
        field = etree.Element('field')
        field.set('name', 'dd_approval_result')
        field.set('decoration-info', "dd_approval_result=='load'")
        field.set('decoration-success', "dd_approval_result=='agree'")
        field.set('decoration-warning', "dd_approval_result=='redirect'")
        field.set('decoration-danger', "dd_approval_result=='refuse'")
        field.set('widget', 'badge')
        field.set('optional', 'show')
        tree.append(field)
    result['arch'] = etree.tostring(tree)


def modify_form_view_header(self, result):
    # 判断是否存在<header>
    print(result)
    arch = etree.fromstring(result['arch'])
    headers = arch.xpath('header')
    if not headers:
        header = etree.Element('header')
        arch.insert(0, header)
    else:
        header = headers[0]
    # 状态栏
    dd_approval_state_field = etree.Element('field')
    dd_approval_state_field.set('name', 'dd_approval_state')
    dd_approval_state_field.set('widget', 'statusbar')
    header.insert(len(header.xpath('button')), dd_approval_state_field)
    # 审批结果
    dd_approval_result_field = etree.Element('field')
    dd_approval_result_field.set('name', 'dd_approval_result')
    dd_approval_result_field.set('modifiers', '{"invisible": true}')
    header.insert(len(header.xpath('button')), dd_approval_result_field)
    # 审批记录按钮
    button_boxs = arch.xpath('//div[@class="oe_button_box"]')
    if not button_boxs:
        sheet = arch.xpath('//sheet')[0]
        button_box = etree.Element('div')
        button_box.set('class', 'oe_button_box')
        button_box.set('name', 'button_box')
        sheet.insert(0, button_box)
    else:
        button_box = button_boxs[0]
    # ----button----
    record_button = etree.Element('button')
    record_button.set('name', 'action_dingtalk_approval_record')
    record_button.set('type', 'object')
    record_button.set('class', 'oe_stat_button')
    record_button.set('icon', 'fa-list')
    record_button.set('string', '审批日志')
    record_button.set('modifiers', '{"invisible": [["dd_approval_state", "=", "draft"]]}')
    button_box.insert(5, record_button)

    # 钉钉审批
    dd_submit_button = etree.Element('button')
    dd_submit_button.set('string', u'提交钉钉审批')
    dd_submit_button.set('class', 'btn-primary')
    dd_submit_button.set('type', 'object')
    dd_submit_button.set('name', 'commit_dingtalk_approval')
    dd_submit_button.set('confirm', '确认提交到钉钉进行审批吗？')
    dd_submit_button.set('modifiers', '{"invisible": [["dd_approval_state", "!=", "draft"]]}')
    header.insert(len(header.xpath('button')), dd_submit_button)

    # 重新提交
    restart_button = etree.Element('button')
    restart_button.set('string', u'重新提交审批')
    restart_button.set('class', 'btn-info')
    restart_button.set('type', 'object')
    restart_button.set('name', 'restart_commit_approval')
    restart_button.set('confirm', '确认重新提交单据至钉钉进行审批吗？')
    restart_button.set('modifiers', '{"invisible": [["dd_approval_result", "in", ["load", "agree", "redirect"]]]}')
    header.insert(len(header.xpath('button')), restart_button)
    # 撤销钉钉审批
    restart_button = etree.Element('button')
    restart_button.set('string', u'撤销钉钉审批')
    restart_button.set('class', 'btn-warning')
    restart_button.set('type', 'object')
    restart_button.set('name', 'terminate_dingtalk_approval')
    restart_button.set('confirm', '确认撤回该单据？')
    restart_button.set('modifiers', '{"invisible": [["dd_approval_state", "!=", "approval"]]}')
    header.insert(len(header.xpath('button')), restart_button)

    # mail.chatter
    # chatter = arch.xpath('//div[@class="oe_chatter"]')
    # if not chatter:
    #     form = arch.xpath('//form')[0]
    #     chatter = etree.SubElement(form, 'div')
    #     chatter.set('class', 'oe_chatter')
    result['arch'] = etree.tostring(arch)


def view_get_approval_view(self, view_type, result):
    if view_type not in ['form', 'tree']:
        return
    approval_control_obj = self.env.get('dingtalk.approval.control').sudo()
    if approval_control_obj is None:
        return
    model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
    domain = [('company_id', '=', self.env.company.id), ('oa_model_id', '=', model_id), ('state', '=', 'open')]
    approval_control = approval_control_obj.with_context(active_test=False).search(domain)
    if approval_control:
        env_context = self.env.context
        if len(approval_control) == 1:
            if not approval_control.model_field_id:
                if view_type == 'tree':
                    return modify_tree_view(self, result)
                else:
                    return modify_form_view_header(self, result)
            context_value = env_context.get(approval_control.model_field_id.name) or env_context.get("default_{}".format(approval_control.model_field_id.name))
            model_field_value = approval_control.model_field_value
            if context_value == model_field_value:
                if view_type == 'tree':
                    return modify_tree_view(self, result)
                else:
                    return modify_form_view_header(self, result)
            else:
                return
        else:
            for flow in approval_control:
                if flow.model_field_id:
                    context_value = env_context.get(flow.model_field_id.name) or env_context.get("default_{}".format(flow.model_field_id.name))
                    model_field_value = flow.model_field_value
                    if context_value == model_field_value:
                        if view_type == 'tree':
                            return modify_tree_view(self, result)
                        else:
                            return modify_form_view_header(self, result)
                else:
                    return
    else:
        return
