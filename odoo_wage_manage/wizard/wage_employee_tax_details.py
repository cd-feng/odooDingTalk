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
    def _alter_date_code(self):
        """
        根据日期生成年份
        :return:
        """
        for res in self:
            if res.start_date:
                res.date_code = str(res.start_date)[:4]

    @api.multi
    def init_employee_tax_details(self):
        """
        初始化员工个税
        :return:
        """
        self.ensure_one()
        raise UserError("暂未实现!")
