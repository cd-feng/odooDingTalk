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


class ComputeWageInsuredMonthlyStatement(models.TransientModel):
    _name = 'compute.wage.insured.monthly.statement'
    _description = "生成员工月结账单"

    monthly_date = fields.Date(string=u'月结日期', required=True)
    date_code = fields.Char(string='期间代码')
    emp_ids = fields.Many2many('hr.employee', string=u'月结员工')
    all_emp = fields.Boolean(string=u'全部员工?')
    
    
    def compute_emp_detail(self):
        """
        生成员工月结账单
        :return:
        """
        self.ensure_one()
        date_code = "{}/{}".format(str(self.monthly_date)[:4], str(self.monthly_date)[5:7])
        # 遍历所有员工
        for emp in self.emp_ids.with_progress(msg="生成员工月结账单"):
            logging.info(">>>生成员工：'%s' 月结账单" % emp.name)
            # 获取员工参保模型
            insured_scheme = self.env['wage.insured.scheme.employee'].search([('employee_id', '=', emp.id)], limit=1)
            monthly_data = {
                'employee_id': emp.id,
                'department_id': emp.department_id.id,
                'monthly_date': str(self.monthly_date),
                'date_code': date_code,
            }
            monthly_line = list()
            if insured_scheme:
                monthly_data.update({'payment_method': insured_scheme.payment_method})
                # 获取参保方案
                scheme = insured_scheme.scheme_id
                # 读取参保方案险种并计算
                for scheme_line in scheme.line_ids:
                    monthly_line.append((0, 0, {
                        'insurance_id': scheme_line.insurance_id.id,
                        'base_number': scheme_line.base_number,
                        'company_pay': scheme_line.base_number * scheme_line.company_number,
                        'pension_pay': scheme_line.base_number * scheme_line.personal_number,
                    }))
            monthly_data.update({'line_ids': monthly_line})
            # 创建月结账单
            domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
            statement = self.env['wage.insured.monthly.statement'].search(domain)
            if statement:
                statement.write({'line_ids': [(2, statement.line_ids.ids)]})
                statement.write(monthly_data)
            else:
                self.env['wage.insured.monthly.statement'].create(monthly_data)
        logging.info(">>>End生成员工月结账单")
        action = self.env.ref('odoo_wage_manage.wage_insured_monthly_statement_action')
        return action.read()[0]

    @api.onchange('monthly_date')
    def _onchagnge_monthly_date(self):
        """
        生成期间代码
        :return:
        """
        if self.monthly_date:
            self.date_code = "{}/{}".format(str(self.monthly_date)[:4], str(self.monthly_date)[5:7])

    @api.onchange('all_emp')
    def onchange_all_emp(self):
        """
        获取全部员工
        :return:
        """
        if self.all_emp:
            employees = self.env['hr.employee'].search([])
            self.emp_ids = [(6, 0, employees.ids)]
