# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt
_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _name = 'hr.department'

    ding_id = fields.Char(string='钉钉Id')
    manager_user_ids = fields.Many2many('hr.employee', 'hr_dept_manage_user_emp_rel', string=u'部门主管')
    is_root = fields.Boolean(string=u'根部门?', default=False)

    @api.model
    def get_department_info(self, department_ids, company):
        """
        获取部门详情
        :param department_ids:
        :param company:
        :return:
        """
        for department_id in department_ids:
            try:
                client = dt.get_client(self, dt.get_dingtalk_config(self, company))
                result = client.department.get(department_id)
            except Exception as e:
                _logger.info("获取部门详情失败：{}".format(e))
                continue
            if result.get('errcode') == 0:
                data = {
                    'name': result.get('name'),
                    'ding_id': department_id,
                    'company_id': company.id,
                }
                if result.get('parentid') != 1:
                    domain = [('ding_id', '=', result.get('parentid')), ('company_id', '=', company.id)]
                    partner_department = self.env['hr.department'].search(domain, limit=1)
                    if partner_department:
                        data.update({'parent_id': partner_department.id})
                else:
                    data['is_root'] = True
                dept_manager_ids = result.get('deptManagerUseridList').split("|")
                manage_users = self.env['hr.employee'].search([('ding_id', 'in', dept_manager_ids), ('company_id', '=', company.id)])
                if manage_users:
                    data.update({
                        'manager_user_ids': [(6, 0, manage_users.ids)],
                        'manager_id': manage_users[0].id
                    })
                domain = [('ding_id', '=', department_id), ('company_id', '=', company.id)]
                h_department = self.env['hr.department'].search(domain)
                if h_department:
                    h_department.write(data)
                else:
                    self.env['hr.department'].create(data)
