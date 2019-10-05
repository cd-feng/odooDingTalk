# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WageEmployeeTaxDetailsTransient(models.TransientModel):
    _name = 'wage.employee.tax.details.transient'
    _description = "初始化员工个税"

    start_date = fields.Date(string=u'年开始日期', required=True)
    end_date = fields.Date(string=u'年结束日期', required=True)
    year = fields.Char(string='年份')
    emp_ids = fields.Many2many('hr.employee', string=u'员工', required=True)
    all_emp = fields.Boolean(string=u'全部员工?')

    @api.onchange('all_emp')
    def onchange_all_emp(self):
        """
        获取全部员工
        :return:
        """
        if self.all_emp:
            employees = self.env['hr.employee'].search([])
            self.emp_ids = [(6, 0, employees.ids)]

    @api.onchange('start_date')
    def _alter_form_year(self):
        """
        根据日期生成年份
        :return:
        """
        for res in self:
            if res.start_date:
                res.date_code = str(res.start_date)[:4]

    def init_employee_tax_details(self):
        """
        初始化员工个税
        :return:
        """
        self.ensure_one()
        year = str(self.start_date)[:4]
        line_list = self._get_detail_line()
        for emp in self.emp_ids.with_progress(msg="初始化员工个税"):
            detail_data = {
                'employee_id': emp.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'year': year,
                'line_ids': line_list,
            }
            domain = [('employee_id', '=', emp.id), ('year', '=', year)]
            details = self.env['wage.employee.tax.details'].sudo().search(domain)
            if not details:
                self.env['wage.employee.tax.details'].create(detail_data)
        action = self.env.ref('odoo_wage_manage.wage_employee_tax_details_action')
        return action.read()[0]

    @api.model
    def _get_detail_line(self):
        # 默认加载12个月份到列表
        line_list = list()
        i = 1
        while i < 13:
            if i < 10:
                line_list.append((0, 0, {
                    'month': "0{}".format(str(i)),
                }))
            else:
                line_list.append((0, 0, {
                    'month': str(i),
                }))
            i += 1
        return line_list
