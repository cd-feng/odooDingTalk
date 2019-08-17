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


class WageSpecialAdditionalDeduction(models.Model):
    _name = 'wage.special.additional.deduction'
    _description = "专项附加扣除"
    _order = 'id'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    start_date = fields.Date(string=u'税款所属期起', required=True, index=True)
    end_date = fields.Date(string=u'税款所属期止', required=True, index=True)
    date_code = fields.Char(string='期间')
    cumulative_expenditure_deduction = fields.Float(string=u'累计子女教育', digits=(10, 2))
    cumulative_support_for_the_elderly = fields.Float(string=u'累计赡养老人', digits=(10, 2))
    cumulative_continuing_education_deduction = fields.Float(string=u'累计继续教育', digits=(10, 2))
    cumulative_home_loan_interest_deduction = fields.Float(string=u'累计住房贷款利息', digits=(10, 2))
    cumulative_housing_rental_expense_deduction = fields.Float(string=u'累计住房租金', digits=(10, 2))
    total_tax_deduction = fields.Float(string=u'个税抵扣总额', digits=(10, 2))
    notes = fields.Text(string=u'备注')

    @api.onchange('start_date')
    @api.constrains('start_date')
    def _alter_date_code(self):
        """
        根据开始日期生成期间代码
        :return:
        """
        for res in self:
            if res.start_date:
                start_date = str(res.start_date)
                res.date_code = "{}/{}".format(start_date[:4], start_date[5:7])

    @api.constrains('employee_id', 'date_code')
    def _constranint_employee(self):
        """
        检查员工同一期间是否存在多条记录
        :return:
        """
        for res in self:
            count_num = self.search_count([('employee_id', '=', res.employee_id.id), ('date_code', '=', res.date_code)])
            if count_num > 1:
                raise UserError("员工{}在{}期间已存在数据，请勿重复录入!".format(res.employee_id.name, res.date_code))
