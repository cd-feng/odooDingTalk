# -*- coding: utf-8 -*-

from lxml import etree
from odoo import models, api


fields_view_get_origin = models.BaseModel.fields_view_get


@api.model
def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    result = fields_view_get_origin(self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    view_get_approval_flow(self, view_type, result)
    return result


models.BaseModel.fields_view_get = fields_view_get


def modify_tree_view(obj, result):
    fields_info = obj.fields_get(allfields=['dd_doc_state', 'dd_approval_state', 'dd_approval_result'])
    if 'dd_doc_state' in fields_info:
        dd_doc_state = fields_info['dd_doc_state']
        dd_doc_state.update({'view': {}})
        result['fields']['dd_doc_state'] = dd_doc_state

        root = etree.fromstring(result['arch'])
        field = etree.Element('field')
        field.set('name', 'dd_doc_state')
        field.set('widget', 'dd_approval_widget')
        root.append(field)
        result['arch'] = etree.tostring(root)

    if 'dd_approval_state' in fields_info:
        dd_approval_state = fields_info['dd_approval_state']
        dd_approval_state.update({'view': {}})
        result['fields']['dd_approval_state'] = dd_approval_state

        root = etree.fromstring(result['arch'])
        field = etree.Element('field')
        field.set('name', 'dd_approval_state')
        field.set('widget', 'badge')
        field.set('optional', 'show')
        field.set('decoration-info', "dd_approval_state=='approval'")
        field.set('decoration-success', "dd_approval_state=='stop'")
        field.set('decoration-warning', "dd_approval_state=='draft'")
        root.append(field)
        result['arch'] = etree.tostring(root)

    if 'dd_approval_result' in fields_info:
        dd_approval_result = fields_info['dd_approval_result']
        dd_approval_result.update({'view': {}})
        result['fields']['dd_approval_result'] = dd_approval_result

        root = etree.fromstring(result['arch'])
        field = etree.Element('field')
        field.set('name', 'dd_approval_result')
        field.set('decoration-info', "dd_approval_result=='load'")
        field.set('decoration-success', "dd_approval_result=='agree'")
        field.set('decoration-warning', "dd_approval_result=='redirect'")
        field.set('decoration-danger', "dd_approval_result=='refuse'")
        field.set('widget', 'badge')
        field.set('optional', 'show')
        root.append(field)
        result['arch'] = etree.tostring(root)
    root = etree.fromstring(result['arch'])
    result['arch'] = etree.tostring(root)


def modify_form_view(self, result):
    # 判断是否存在<header>
    root = etree.fromstring(result['arch'])
    headers = root.xpath('header')
    if not headers:
        header = etree.Element('header')
        root.insert(0, header)
    else:
        header = headers[0]
    # 状态栏
    dd_approval_state_field = etree.Element('field')
    dd_approval_state_field.set('name', 'dd_approval_state')
    dd_approval_state_field.set('widget', 'statusbar')
    dd_approval_state_field.set('modifiers', '{"readonly": true}')
    header.insert(len(header.xpath('button')), dd_approval_state_field)
    # 审批结果
    dd_approval_result_field = etree.Element('field')
    dd_approval_result_field.set('name', 'dd_approval_result')
    dd_approval_result_field.set('modifiers', '{"invisible": true}')
    header.insert(len(header.xpath('button')), dd_approval_result_field)
    # 审批记录按钮
    button_boxs = root.xpath('//div[@class="oe_button_box"]')
    if not button_boxs:
        sheet = root.xpath('//sheet')[0]
        button_box = etree.SubElement(sheet, 'div')
        button_box.set('class', 'oe_button_box')
        button_box.set('name', 'button_box')
    else:
        button_box = button_boxs[0]
    # ----button----
    record_button = etree.Element('button')
    record_button.set('name', 'action_dingtalk_approval_record')
    record_button.set('string', '审批记录')
    record_button.set('type', 'object')
    record_button.set('class', 'oe_stat_button')
    record_button.set('icon', 'fa-list-alt')
    button_box.insert(1, record_button)

    # 钉钉审批
    dd_submit_button = etree.Element('button')
    dd_submit_button.set('string', u'钉钉审批')
    dd_submit_button.set('class', 'btn-primary')
    dd_submit_button.set('type', 'object')
    dd_submit_button.set('name', 'commit_dingtalk_approval')
    dd_submit_button.set('confirm', '确认提交到钉钉进行审批吗？')
    dd_submit_button.set('modifiers', '{"invisible": [["dd_approval_state", "!=", "draft"]]}')
    header.insert(len(header.xpath('button')), dd_submit_button)
    # 重新提交
    restart_button = etree.Element('button')
    restart_button.set('string', u'重新提交')
    restart_button.set('class', 'btn-primary')
    restart_button.set('type', 'object')
    restart_button.set('name', 'restart_commit_approval')
    restart_button.set('confirm', '确认重新提交单据至钉钉进行审批吗？ *_*!')
    restart_button.set('modifiers', '{"invisible": [["dd_approval_result", "not in", ["refuse"]]]}')
    header.insert(len(header.xpath('button')), restart_button)
    # mail.chatter
    chatter = root.xpath('//div[@class="oe_chatter"]')
    if not chatter:
        form = root.xpath('//form')[0]
        chatter = etree.SubElement(form, 'div')
        chatter.set('class', 'oe_chatter')
    result['arch'] = etree.tostring(root)


def view_get_approval_flow(self, view_type, result):
    if view_type not in ['form', 'tree']:
        return
    flow_obj = self.env.get('dingtalk.approval.control')
    if flow_obj is None:
        return
    model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
    domain = [('company_id', '=', self.env.user.company_id.id), ('oa_model_id', '=', model_id)]
    flows = flow_obj.with_context(active_test=False).sudo().search(domain)
    if not flows:
        return
    if view_type == 'tree':
        modify_tree_view(self, result)
    if view_type == 'form':
        modify_form_view(self, result)


