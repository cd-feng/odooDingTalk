# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api, exceptions
from ..tools.dingtalk_hr import DingTalkHr
_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dingtalk_id = fields.Integer(string='钉钉部门ID', index=True)
    dingtalk_parent_id = fields.Integer(string='父部门ID', index=True)

    @api.model
    def request_dingtalk_department_data(self, company_id):
        """
        从钉钉中同步获取所有部门数据
        """
        conf_id = self.env['dingtalk.setting'].sudo().get_setting_param(company_id)
        if not conf_id:
            raise exceptions.UserError("请先配置钉钉应用API参数！")
        try:
            client = DingTalkHr(app_key=conf_id.app_key, app_secret=conf_id.app_secret)
            return client.get_department_list()
        except Exception as e:
            raise e

    @api.model
    def update_dingtalk_department_data(self, department_data, company_id):
        """
        更新钉钉部门数据
        """
        department_list = department_data.get('department', [])
        if not department_list:
            _logger.warning("未收到任何部门数据，跳过更新...")
            return
        model = self.env['hr.department'].sudo()
        # 预加载已有的部门数据（减少数据库查询）
        existing_departments = model.search_read([('company_id', '=', company_id)], ['id', 'dingtalk_id', 'parent_id'])
        department_dict = {dept['dingtalk_id']: dept['id'] for dept in existing_departments if dept.get('dingtalk_id')}
        new_dept_values, updated_dept_ids = [], []
        # 处理部门数据（新增/更新）
        for data in department_list:
            dingtalk_id, name = data['id'], data['name']
            values = {
                'company_id': company_id,
                'name': name,
                'dingtalk_id': dingtalk_id,
                'dingtalk_parent_id': data.get('parentid'),
            }
            if dingtalk_id in department_dict:
                updated_dept_ids.append((department_dict[dingtalk_id], values))
            else:
                new_dept_values.append(values)
        # 批量更新已有部门
        if updated_dept_ids:
            for dept_id, values in updated_dept_ids:
                model.browse(dept_id).write(values)
        # 批量创建新部门
        if new_dept_values:
            new_departments = model.create(new_dept_values)
            department_dict.update({dept.dingtalk_id: dept.id for dept in new_departments})
        self.env.cr.commit()  # 提交事务，提高稳定性
        for data in department_list:
            dingtalk_id, parentid = data.get('id'), data.get('parentid')
            if parentid and parentid in department_dict and dingtalk_id in department_dict:
                model.browse(department_dict[dingtalk_id]).write({'parent_id': department_dict[parentid]})

