# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _name = 'hr.department'

    ding_id = fields.Char(string='钉钉Id', index=True)
    manager_user_ids = fields.Many2many('hr.employee', 'hr_dept_manage_user_emp_rel', string=u'部门主管')
    is_root = fields.Boolean(string=u'根部门?', default=False)

    def create_ding_department(self):
        if not self.user_has_groups('dingtalk_mc.manage_groups'):
            raise UserError("您没有创建/上传到钉钉部门的权限！")
        for res in self:
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            if res.ding_id:
                raise UserError("部门:(%s)已存在了钉钉ID，不能再进行上传。" % res.name)
            data = {'name': res.name}
            # 获取父部门ding_id
            if res.is_root:
                data.update({'parentid': 1})
            else:
                if res.parent_id:
                    data.update({'parentid': res.parent_id.ding_id if res.parent_id.ding_id else ''})
                else:
                    raise UserError("请选择上级部门或则根部门。")
            try:
                result = client.department.create(data)
                res.write({'ding_id': result})
                res.message_post(body=u"上传钉钉成功。", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def update_ding_department(self):
        if not self.user_has_groups('dingtalk_mc.manage_groups'):
            raise UserError("您没有修改/更新到钉钉部门的权限！")
        for res in self:
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            data = {
                'id': res.ding_id,  # id
                'name': res.name,  # 部门名称
                'parentid': res.parent_id.ding_id,  # 父部门id
            }
            if res.is_root:
                data.update({'parentid': 1})
            try:
                result = client.department.update(data)
                _logger.info(result)
                res.message_post(body=u"更新钉钉部门成功", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def delete_ding_department(self):
        if not self.user_has_groups('dingtalk_mc.manage_groups'):
            raise UserError("您没有删除钉钉部门的权限！")
        for res in self:
            if not res.ding_id:
                continue
            self._delete_dingtalk_department_by_id(res.ding_id, self.company_id)
            res.write({'ding_id': False})
            res.message_post(body=u"已在钉钉上删除部门。", message_type='notification')
        return {'type': 'ir.actions.act_window_close'}

    def unlink(self):
        for res in self:
            if res.ding_id and dt.get_config_is_delete(self, res.company_id):
                self._delete_dingtalk_department_by_id(res.ding_id, res.company_id)
        return super(HrDepartment, self).unlink()

    def _delete_dingtalk_department_by_id(self, ding_id, company):
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            result = client.department.delete(ding_id)
            _logger.info("已在钉钉上删除Id:{}的部门".format(result))
        except Exception as e:
            raise UserError(e)
        return

    @api.model
    def process_dingtalk_chat(self, result_msg, company):
        """
        接受来自钉钉回调的处理
        :param result_msg: 回调消息
        :param company: 公司
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                event_type = result_msg.get('EventType')  # 消息类型
                dept_ids = result_msg.get('DeptId')
                if event_type == 'org_dept_remove':
                    departments = self.env['hr.department'].sudo().search([('ding_id', 'in', dept_ids), ('company_id', '=', company.id)])
                    if departments:
                        departments.sudo().write({'active': False})
                else:
                    # 部门增加和变更时获取该部门详情
                    for dept_id in dept_ids:
                        self.get_department_info(dept_id, event_type, company)
        return True

    @api.model
    def get_department_info(self, dept_id, event_type, company):
        """
        获取部门详情
        :param dept_id:
        :param event_type:
        :param company:
        :return:
        """
        try:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            result = client.department.get(dept_id)
        except Exception as e:
            _logger.info("获取部门详情失败：{}".format(e))
            return
        if result.get('errcode') == 0:
            data = {
                'name': result.get('name'),
                'ding_id': result.get('id'),
                'company_id': company.id,
            }
            if result.get('parentid') != 1:
                domain = [('ding_id', '=', result.get('parentid')), ('company_id', '=', company.id)]
                partner_department = self.env['hr.department'].sudo().search(domain, limit=1)
                if partner_department:
                    data.update({'parent_id': partner_department.id})
            else:
                data['is_root'] = True
            depts = result.get('deptManagerUseridList').split("|")
            manage_users = self.env['hr.employee'].sudo().search([('ding_id', 'in', depts), ('company_id', '=', company.id)])
            if manage_users:
                data.update({
                    'manager_user_ids': [(6, 0, manage_users.ids)],
                    'manager_id': manage_users[0].id
                })
            domain = [('ding_id', '=', result.get('id')), ('company_id', '=', company.id)]
            if event_type == 'org_dept_create':
                h_department = self.env['hr.department'].sudo().search(domain)
                if not h_department:
                    self.env['hr.department'].sudo().create(data)
            elif event_type == 'org_dept_modify':
                h_department = self.env['hr.department'].sudo().search(domain)
                if h_department:
                    h_department.sudo().write(data)
        return True
