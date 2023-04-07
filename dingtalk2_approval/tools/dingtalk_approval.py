# -*- coding: utf-8 -*-
import logging
import pendulum
from odoo import models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt

_logger = logging.getLogger(__name__)


def submit_dingtalk_approval(self, approval, res_company):
    """
    提交到钉钉进行审批
    :param self: 当前操作的对象
    :param approval: 审批配置模型
    :param res_company: 公司对象
    :return:（钉钉返回的结果, 钉钉审批配置模型）
    """
    _logger.info(">: 准备提交'%s'的审批单据至钉钉进行审批..." % approval.name)
    # 获取表单参数
    form_values = get_form_values(self, approval)
    # 发起人和发起人部门
    user_id, dept_id = get_originator_user_id(self, res_company.id)
    # 获取审批人和抄送人列表
    approvers_users = approval.get_approvers_users()
    cc_users, cc_type = approval.get_cc_users()
    data = {
        'process_code': approval.template_id.process_code,  # 审批模型编号
        'originator_user_id': user_id,  # 发起人
        'dept_id': dept_id,             # 发起部门
        'form_component_values': form_values  # 表单参数
    }
    if approvers_users:
        if approval.approval_type == 'turn':
            data.update({'approvers': approvers_users})   # 依次审批人列表
        else:
            data.update({'approvers_v2': approvers_users})  # 会签、或签审批人列表
    if cc_users and cc_type:
        data.update({
            'cc_list': cc_users,     # 抄送列表
            'cc_position': cc_type     # 抄送时间
        })
    # ----提交至钉钉---
    client = dt.get_client(self, dt.get_dingtalk2_config(self, res_company))
    try:
        result = client.post('topapi/processinstance/create', data)
    except Exception as e:
        raise UserError(e)
    _logger.info(result)
    return result


def get_dingtalk_approval(self):
    """
    返回审批配置模型
    :param self:
    :return:
    """
    try:
        res_company = self.company_id
    except Exception:
        res_company = self.env.company
    res_company_id = res_company.id
    # 获取审批配置
    model_id = self.env['ir.model'].with_user(SUPERUSER_ID).search([('model', '=', self._name)]).id
    domain = [('oa_model_id', '=', model_id), ('company_id', '=', res_company_id), ('state', '=', 'open')]
    approval_control = self.env['dingtalk.approval.control'].with_user(SUPERUSER_ID).search(domain)
    approval = None
    if len(approval_control) == 1:
        approval = approval_control[0]
    elif len(approval_control) > 1:
        for ac in approval_control:
            if ac.model_field_id and self[ac.model_field_id.name] == ac.model_field_value:
                approval = ac
                break
    else:
        raise UserError('没有找到本模型对应的钉钉工作流配置，请联系管理员配置后再试。')
    return approval, res_company


def _commit_dingtalk_approval(self):
    """
    钉钉提交审批
    :param self:
    :return:
    """
    self.ensure_one()
    if self.dd_approval_state == 'approval':
        raise ValidationError("当前单据已提交至钉钉审批或审批已完结，请勿重复提交，建议刷新页面或再次点击菜单进入查看最新状态！")
    approval, res_company = get_dingtalk_approval(self)
    model_name = self._name.replace('.', '_')
    # 判断条件
    if approval.approval_domain:
        domain = [('id', '=', self.id)]
        domain += eval(approval.approval_domain)
        result = self.with_user(SUPERUSER_ID).search(domain)
        if not result:
            # 无需提交到钉钉进行审批
            sql = """UPDATE {} SET dd_approval_state='{}', dd_doc_state='{}', dd_approval_result='{}' WHERE id={}""".format(model_name, 'stop', '无需审批', 'agree', self.id)
            self._cr.execute(sql)
            try:
                self.message_post(body="单据无需提交至钉钉审批，已默认为审批通过。", message_type='notification')
            except Exception as e:
                _logger.info(">>> 发送消息备注失败：{}".format(str(e)))
            _logger.info(message="单据无需提交至钉钉审批，已默认为审批通过！", sticky=True)
            return True
    result = submit_dingtalk_approval(self, approval, res_company)
    if result.get('errcode') != 0:
        raise UserError('提交审批实例失败，失败原因:{}'.format(result.get('errmsg')))
    sql = """UPDATE {} SET dd_approval_state='{}', dd_doc_state='{}', dd_process_instance='{}' 
             WHERE id={}""".format(model_name, 'approval', '等待审批', result.get('process_instance_id'), self.id)
    self._cr.execute(sql)
    # ------执行提交审批运行函数代码-------
    if approval.approval_start_function:
        for method in approval.approval_start_function.split(','):
            try:
                getattr(self, method)()
            except Exception as e:
                _logger.info("运行自定义审批函数失败，原因：{}".format(str(e)))
    try:
        self.message_post(body="提交钉钉成功，请等待审批人进行审批！", message_type='notification')
    except Exception as e:
        _logger.info(">>> 发送消息备注失败：{}".format(str(e)))
    _logger.info("已提交至钉钉，请等待审批完成！")
    # self.env.user.notify_success(message="已提交至钉钉，请等待审批完成！", sticky=False)
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
                try:
                    fcv_list.append({'name': line.dd_field, 'value': ding_field.name})
                except Exception:
                    fcv_list.append({'name': line.dd_field, 'value': ding_field.with_user(SUPERUSER_ID).name_get()[0][1]})
        # many2many类型
        elif line.ttype == 'many2many':
            many_models = self[line.field_id.name]
            line_list = list()
            for many_model in many_models:
                # 判断是否为关联组件
                if line.is_dd_id:
                    line_list.append(many_model.ding_id)
                else:
                    try:
                        line_list.append(many_model.name)
                    except Exception:
                        line_list.append(many_model.with_user(SUPERUSER_ID).name_get()[0][1])
            fcv_list.append({'name': line.dd_field, 'value': line_list})
        # date类型
        elif line.ttype == 'date':
            old_date = self[line.field_id.name]
            try:
                bj_datetime = pendulum.parse(old_date.strftime('%Y-%m-%d')).add(hours=8)
            except AttributeError:
                bj_datetime = pendulum.today()
            fcv_list.append({'name': line.dd_field, 'value': bj_datetime.format("YYYY-MM-DD")})
        # datetime类型
        elif line.ttype == 'datetime':
            old_date = self[line.field_id.name]
            try:
                bj_datetime = pendulum.parse(old_date.strftime('%Y-%m-%d %H:%M')).add(hours=8)
            except AttributeError:
                bj_datetime = pendulum.today()
            fcv_list.append({'name': line.dd_field, 'value': bj_datetime.format("YYYY-MM-DD HH:mm")})
        # char、text、integer、float、monetary类型
        elif line.ttype in ['char', 'text', 'integer', 'float', 'monetary']:
            fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name]})
        # selection类型
        elif line.ttype in ['selection']:
            model_name = line.model_id.model
            field_name = line.field_id.name
            type_dict = dict(self.env[model_name].fields_get(allfields=[field_name])[field_name]['selection'])
            fcv_list.append({'name': line.dd_field, 'value': type_dict.get(self[line.field_id.name])})
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
                            try:
                                fcv_line_list.append({'name': list_id.dd_field, 'value': list_ding_field.name})
                            except Exception:
                                fcv_line_list.append({'name': list_id.dd_field, 'value': list_ding_field.with_user(SUPERUSER_ID).name_get()[0][1]})
                    # many2many类型
                    elif list_id.field_id.ttype == 'many2many':
                        list_id_models = model_line[list_id.field_id.name]
                        field_list = list()
                        for list_id_model in list_id_models:
                            # 再判断是否为关联组件
                            if list_id.is_dd_id:
                                field_list.append(list_id_model.ding_id)
                            else:
                                try:
                                    field_list.append(list_id_model.name)
                                except Exception:
                                    field_list.append(list_id_model.with_user(SUPERUSER_ID).name_get()[0][1])
                        fcv_line_list.append({'name': list_id.dd_field, 'value': field_list})
                    # date类型
                    elif list_id.field_id.ttype == 'date':
                        old_date = model_line[list_id.field_id.name]
                        try:
                            line_bj_datetime = pendulum.parse(old_date.strftime('%Y-%m-%d')).add(hours=8)
                        except AttributeError:
                            line_bj_datetime = pendulum.today()
                        fcv_line_list.append({'name': list_id.dd_field, 'value': line_bj_datetime.format("YYYY-MM-DD")})
                    # datetime类型
                    elif list_id.field_id.ttype == 'datetime':
                        old_date = model_line[list_id.field_id.name]
                        try:
                            line_bj_datetime = pendulum.parse(old_date.strftime('%Y-%m-%d %H:%M')).add(hours=8)
                        except AttributeError:
                            line_bj_datetime = pendulum.today()
                        fcv_line_list.append(
                            {'name': list_id.dd_field, 'value': line_bj_datetime.format("YYYY-MM-DD HH:mm")})
                    # char、text、integer、float、monetary类型
                    elif list_id.field_id.ttype in ['char', 'text', 'integer', 'float', 'monetary']:
                        fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name]})
                    # selection类型
                    elif list_id.field_id.ttype in ['selection']:
                        model_name = list_id.field_id.model_id.model
                        field_name = list_id.field_id.name
                        type_dict = dict(self.env[model_name].fields_get(allfields=[field_name])[field_name]['selection'])
                        fcv_line_list.append({'name': list_id.dd_field, 'value': type_dict.get(model_line[list_id.field_id.name])})
                fcv_line.append(fcv_line_list)
            fcv_list.append({'name': line.dd_field, 'value': fcv_line})
    return fcv_list


def get_originator_user_id(self, company_id):
    """
    获取发起人和发起部门
        获取当期登录用户对应的员工钉钉id和部门钉钉id
    :return:
    """
    emp = self.env['hr.employee'].with_user(SUPERUSER_ID).search([('user_id', '=', self.env.user.id), ('company_id', '=', company_id)], limit=1)
    if len(emp) > 1:
        raise UserError("当前登录用户关联了{}个员工，不支持将多员工提交到钉钉审批，请重新关联员工后在进行提交！".format(len(emp)))
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
    if self.dd_approval_state == 'approval':
        raise ValidationError("当前单据已提交至钉钉审批或审批已完结，请勿重复提交，建议刷新页面或再次点击菜单进入查看最新状态！")
    approval, res_company = get_dingtalk_approval(self)
    model_name = self._name.replace('.', '_')
    # 判断条件
    if approval.approval_domain:
        domain = [('id', '=', self.id)]
        domain += eval(approval.approval_domain)
        result = self.with_user(SUPERUSER_ID).search(domain)
        if not result:
            # 无需提交到钉钉进行审批
            sql = """UPDATE {} SET dd_approval_state='{}', dd_doc_state='{}', dd_approval_result='{}' WHERE id={}""".format(
                model_name, 'stop', '无需审批', 'agree', self.id)
            self._cr.execute(sql)
            try:
                self.message_post(body="单据无需提交至钉钉审批，已默认为审批通过。", message_type='notification')
            except Exception as e:
                _logger.info(">>> 发送消息备注失败：{}".format(str(e)))
            _logger.info("该单据无需提交至钉钉审批，已默认为审批通过！")
            return
    result = submit_dingtalk_approval(self, approval, res_company)
    if result.get('errcode') != 0:
        raise UserError('重新提交失败，失败原因:{}'.format(result.get('errmsg')))
    sql = """UPDATE {} 
             SET 
                 dd_approval_state='{}', 
                 dd_doc_state='{}', 
                 dd_approval_result='load', 
                 dd_process_instance='{}' 
             WHERE 
                 id={}""".format(model_name, 'approval', '重新提交审批', result.get('process_instance_id'), self.id)
    self._cr.execute(sql)
    # ------执行重新提交后的函数代码-------
    if approval.approval_restart_function:
        for method in approval.approval_restart_function.split(','):
            try:
                getattr(self, method)()
            except Exception as e:
                _logger.info("运行自定义审批函数失败，原因：{}".format(str(e)))
    try:
        self.message_post(body="已重新提交，请等待审批人审批！", message_type='notification')
    except Exception as e:
        _logger.info(">>> 重新提交审批时发送消息备注失败：{}".format(str(e)))
    _logger.info("已重新提交至钉钉，请等待审批完成！")
    return True


setattr(Model, 'restart_commit_approval', _restart_commit_approval)


def _terminate_dingtalk_approval(self):
    """
    撤回该审批单据
    :param self:
    :return:
    """
    self.ensure_one()
    if self.dd_approval_state != 'approval':
        raise UserError('该单据不是正在审批的单据，可能已被撤回，请刷新当前界面重试！')
    data = {
        'request': {
            'process_instance_id': self.dd_process_instance,
            'is_system': True,
            'remark': "单据已由{}手动撤回！".format(self.env.user.name),
        }
    }
    # ----提交至钉钉---
    client = dt.get_client(self, dt.get_dingtalk2_config(self, self.env.company))
    try:
        result = client.post('topapi/process/instance/terminate', data)
    except Exception as e:
        raise UserError(e)
    _logger.info(result)
    if result.get('result'):
        self.write({
            'dd_approval_state': 'stop',
            'dd_doc_state': '已手动撤回申请',
            'dd_approval_result': 'terminate',
        })
        try:
            self.message_post(body="已手动撤回了申请！", message_type='notification')
        except Exception as e:
            pass
        _logger.info("您已手动撤回了申请")
    else:
        raise UserError('手动撤回失败，原因: {}'.format(result.get('errmsg')))
    return True


setattr(Model, 'terminate_dingtalk_approval', _terminate_dingtalk_approval)


def _action_dingtalk_approval_record(self):
    """
    跳转到钉钉审批记录tree
    :param self:
    :return:
    """
    return {
        "name": "审批记录",
        'type': 'ir.actions.act_window',
        'view_mode': 'tree',
        'res_model': 'dingtalk.approval.log',
        'target': 'new',
        'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
    }


setattr(Model, 'action_dingtalk_approval_record', _action_dingtalk_approval_record)



