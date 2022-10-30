# -*- coding: utf-8 -*-
from odoo import fields, models, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    ding_id = fields.Char(string='钉钉ID')
    manager_user_ids = fields.Many2many(comodel_name="hr.employee", string="部门主管")

    @api.model
    def processing_dingtalk_dept_result(self, data, company_id):
        """
        处理钉钉请求后的数据，封装为odoo部门格式，用于创建或修改
        """
        value = {
            'company_id': company_id,
            'name': data.get('name'),
            'ding_id': data.get('dept_id'),
        }
        parent_id = data.get('parent_id')
        if parent_id != 1:
            parent_dept = self.get_dingtalk_department_id(parent_id, company_id)
            if parent_dept:
                value['parent_id'] = parent_dept.id
        # 部门主管
        manager_user_ids = self.search([('ding_id', 'in', data.get('dept_manager_userid_list'))])
        if manager_user_ids:
            value['manager_user_ids'] = [(6, 0, manager_user_ids.ids)]
        return value

    @api.model
    def get_dingtalk_department_id(self, dept_id, company_id):
        """
        根据钉钉ID获取部门实例
        """
        domain = [('ding_id', '=', dept_id), ('company_id', '=', company_id)]
        return self.env['hr.department'].search(domain, limit=1)
