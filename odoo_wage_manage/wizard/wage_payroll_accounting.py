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


class WagePayrollAccountingTransient(models.TransientModel):
    _name = 'wage.payroll.accounting.transient'
    _description = "薪资计算"

    wage_date = fields.Date(string=u'核算月份', required=True)
    date_code = fields.Char(string='期间代码')
    emp_ids = fields.Many2many('hr.employee', string=u'员工')
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

    @api.onchange('wage_date')
    def _alter_date_code(self):
        """
        根据日期生成期间代码
        :return:
        """
        for res in self:
            if res.wage_date:
                wage_date = str(res.wage_date)
                res.date_code = "{}/{}".format(wage_date[:4], wage_date[5:7])

    @api.multi
    def compute_payroll_accounting(self):
        """
        计算薪资
        :return:
        """
        self.ensure_one()
        raise UserError("暂未实现!")


class PayrollAccountingToPayslipTransient(models.TransientModel):
    _name = 'wage.payroll.accounting.to.payslip.transient'
    _description = "生成工资条"

    start_date = fields.Date(string=u'所属期起', required=True)
    end_date = fields.Date(string=u'所属期止', required=True)
    date_code = fields.Char(string='期间')
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
    def _alter_date_code(self):
        """
        根据日期生成期间代码
        :return:
        """
        for res in self:
            if res.start_date:
                start_date = str(res.start_date)
                res.date_code = "{}/{}".format(start_date[:4], start_date[5:7])

    @api.multi
    def create_employee_payslip(self):
        """
        生成工资条
        :return:
        """
        self.ensure_one()
        raise UserError("暂未实现!")
