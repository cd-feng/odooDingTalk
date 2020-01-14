# -*- coding: utf-8 -*-

import logging
from odoo import models, api
from odoo.exceptions import UserError
from . import dingtalk_api

_logger = logging.getLogger(__name__)


def approval_result(self):
    """
    发起审批
    :param self:
    :return:
    """
    # 获取钉钉审批配置
    model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
    approval = self.env['dingtalk.approval.control'].sudo().search([('oa_model_id', '=', model_id)], limit=1)
    _logger.info("提交'%s'单据至钉钉进行审批..." % approval.name)
    # 钉钉审批模型编码
    process_code = approval.template_id.process_code
    # 发起人和发起人部门
    user_id, dept_id = get_originator_user_id(self)
    # 获取表单参数
    form_values = get_form_values(self, approval)
    _logger.info(form_values)
    # ----提交至钉钉---
    client = dingtalk_api.get_client(self)
    try:
        url = 'topapi/processinstance/create'
        result = client.post(url, {
            'process_code': process_code,
            'originator_user_id': user_id,
            'dept_id': dept_id,
            'form_component_values': form_values  # 表单参数
        })
    except Exception as e:
        raise UserError(e)
    _logger.info(result)
    return result, approval


def _commit_dingtalk_approval(self):
    """
    钉钉提交审批
    :param self:
    :return:
    """
    self.ensure_one()
    result, approval = approval_result(self)
    if result.get('errcode') != 0:
        raise UserError('提交审批实例失败，失败原因:{}'.format(result.get('errmsg')))
    model_name = self._name.replace('.', '_')
    sql = """UPDATE {} 
                SET 
                    dd_approval_state='{}', 
                    dd_doc_state='{}', 
                    dd_process_instance='{}' 
                WHERE 
                    id={}""".format(model_name, 'approval', '等待审批', result.get('process_instance_id'), self.id)
    self._cr.execute(sql)
    # 执行审批运行函数代码
    if approval.approval_start_function:
        for method in approval.approval_start_function.split(','):
            try:
                getattr(self, method)()
            except Exception as e:
                _logger.info(e)
    self.message_post(body=u"提交钉钉成功，请等待审批人进行审批！", message_type='notification')
    return True


Model = models.Model
setattr(Model, 'commit_dingtalk_approval', _commit_dingtalk_approval)


def get_form_values(self, approval):
    """
    获取表单的参数，按照钉钉参数格式进行封装
    :param self:
    :param approval: 审批配置模型
    :return:
    """
    fcv_list = list()
    for line in approval.line_ids:
        # many2one类型字段，只获取name
        if line.ttype == 'many2one':
            ding_field = self[line.field_id.name]
            if line.is_dd_id:
                fcv_list.append({'name': line.dd_field, 'value': [ding_field.ding_id]})
            else:
                fcv_list.append({'name': line.dd_field, 'value': ding_field.name})
        # many2many类型
        elif line.ttype == 'many2many':
            many_models = self[line.field_id.name]
            line_list = list()
            for many_model in many_models:
                # 判断是否为关联组件
                if line.is_dd_id:
                    line_list.append(many_model.ding_id)
                else:
                    line_list.append(many_model.name)
            fcv_list.append({'name': line.dd_field, 'value': line_list})
        # date类型
        elif line.ttype == 'date':
            fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d')})
        # datetime类型
        elif line.ttype == 'datetime':
            fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d %H:%M')})
        # char、text、integer、float、monetary、selection类型
        elif line.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
            fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name]})
        # one2many类型
        elif line.ttype == 'one2many':
            model_lines = self[line.field_id.name]
            fcv_line = list()   # 子表容器列表
            for model_line in model_lines:      # 遍历对象示例列表
                fcv_line_list = list()
                for list_id in line.list_ids:   # 遍历配置项中的字段列表字段
                    # many2one类型字段，只获取name
                    if list_id.field_id.ttype == 'many2one':
                        list_ding_field = model_line[list_id.field_id.name]
                        if list_id.is_dd_id:
                            fcv_line_list.append({'name': list_id.dd_field, 'value': [list_ding_field.ding_id]})
                        else:
                            fcv_line_list.append({'name': list_id.dd_field, 'value': list_ding_field.name})
                    # many2many类型
                    elif list_id.field_id.ttype == 'many2many':
                        list_id_models = model_line[list_id.field_id.name]
                        field_list = list()
                        for list_id_model in list_id_models:
                            # 再判断是否为关联组件
                            if list_id.is_dd_id:
                                field_list.append(list_id_model.ding_id)
                            else:
                                field_list.append(list_id_model.name)
                        fcv_line_list.append({'name': list_id.dd_field, 'value': field_list})
                    # date类型
                    elif list_id.field_id.ttype == 'date':
                        fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d')})
                    # datetime类型
                    elif list_id.field_id.ttype == 'datetime':
                        fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d %H:%M')})
                    # char、text、integer、float、monetary、selection类型
                    elif list_id.field_id.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
                        fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name]})
                fcv_line.append(fcv_line_list)
            fcv_list.append({'name': line.dd_field, 'value': fcv_line})
    return fcv_list


def get_originator_user_id(self):
    """
    获取发起人和发起部门
        获取当期登录用户对应的员工钉钉id和部门钉钉id
    :return:
    """
    emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
    if not emp:
        raise UserError("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")
    if not emp.ding_id:
        raise UserError("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format(emp.name))
    if not emp.department_id:
        raise UserError("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format(emp.name))
    if not emp.department_id.ding_id:
        raise UserError("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format(emp.name, emp.department_id.name))
    return emp.ding_id, emp.department_id.ding_id


def _restart_commit_approval(self):
    """
    重新提交至钉钉审批
    :param self:
    :return:
    """
    self.ensure_one()
    result, approval = approval_result(self)
    if result.get('errcode') != 0:
        raise UserError('重新提交失败，失败原因:{}'.format(result.get('errmsg')))
    model_name = self._name.replace('.', '_')
    sql = """UPDATE {} 
             SET 
                 dd_approval_state='{}', 
                 dd_doc_state='{}', 
                 dd_approval_result='load', 
                 dd_process_instance='{}' 
             WHERE 
                 id={}""".format(model_name, 'approval', '重新提交审批', result.get('process_instance_id'), self.id)
    self._cr.execute(sql)
    self.message_post(body=u"已重新提交，请等待审批人审批！", message_type='notification')
    return True


setattr(Model, 'restart_commit_approval', _restart_commit_approval)


