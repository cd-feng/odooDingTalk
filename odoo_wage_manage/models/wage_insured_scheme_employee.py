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

_logger = logging.getLogger(__name__)


class WageInsuredSchemeEmployee(models.Model):
    _description = '参保员工'
    _name = 'wage.insured.scheme.employee'
    _rec_name = 'employee_id'
    _order = 'id'

    active = fields.Boolean(string=u'Active', default=True)
    payment_method = fields.Selection(string=u'缴纳方式', selection=[('company', '公司自缴'), ('other', '其他'), ], default='company')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id, index=True, required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'参保员工', index=True, copy=False)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'所属部门', index=True, copy=False)
    scheme_id = fields.Many2one(comodel_name='wage.insured.scheme', string=u'参保方案')
    social_security_start_date = fields.Date(string=u'社保起始日期')
    public_fund_start_date = fields.Date(string=u'公积金起始日期')
    notes = fields.Text(string=u'备注')

