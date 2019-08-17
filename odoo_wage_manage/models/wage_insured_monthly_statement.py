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


class WageInsuredMonthlyStatement(models.Model):
    _description = '员工月结账单'
    _name = 'wage.insured.monthly.statement'
    _rec_name = 'name'
    _order = 'date_code'

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char(string='名称')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id, index=True, required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'参保员工', required=True, index=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'员工部门', index=True)
    monthly_date = fields.Date(string=u'月结日期', required=True)
    date_code = fields.Char(string='期间代码', index=True)
    payment_method = fields.Selection(string=u'缴纳方式', selection=[('company', '公司自缴'), ('other', '其他')], default='company')
    line_ids = fields.One2many('wage.insured.monthly.statement.line', 'statement_id', string=u'账单明细')
    personal_sum = fields.Float(string=u'个人缴纳总计', digits=(10, 4), compute='_compute_statement_sum')
    company_sum = fields.Float(string=u'公司缴纳合计', digits=(10, 4), compute='_compute_statement_sum')
    notes = fields.Text(string=u'备注')

    @api.constrains('employee_id', 'monthly_date')
    def _constrains_name(self):
        """
        生成name字段
        :return:
        """
        for res in self:
            if res.employee_id and res.monthly_date:
                res.name = "{}&{}".format(res.employee_id.name, str(res.monthly_date)[:7])

    @api.onchange('monthly_date')
    @api.constrains('monthly_date')
    def _alter_date_code(self):
        """
        根据日期生成期间代码
        :return:
        """
        for res in self:
            if res.monthly_date:
                monthly_date = str(res.monthly_date)
                res.date_code = "{}/{}".format(monthly_date[:4], monthly_date[5:7])

    def _compute_statement_sum(self):
        """
        公司缴纳合计、个人缴纳总计
        :return:
        """
        for res in self:
            personal_sum = company_sum = 0
            for line in res.line_ids:
                company_sum += line.company_pay
                personal_sum += line.pension_pay
            res.update({
                'company_sum': company_sum,
                'personal_sum': personal_sum,
            })


class WageInsuredMonthlyStatementLine(models.Model):
    _description = '月结账单明细'
    _name = 'wage.insured.monthly.statement.line'

    sequence = fields.Integer(string=u'序号')
    statement_id = fields.Many2one(comodel_name='wage.insured.monthly.statement', string=u'员工月结账单', ondelete='cascade')
    insurance_id = fields.Many2one(comodel_name='wage.insured.scheme.insurance', string=u'险种', required=True)
    base_number = fields.Float(string=u'险种基数', digits=(10, 2))
    company_pay = fields.Float(string=u'公司缴纳', digits=(10, 4))
    pension_pay = fields.Float(string=u'个人缴纳', digits=(10, 4))
