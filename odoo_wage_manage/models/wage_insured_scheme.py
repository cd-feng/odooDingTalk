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


class WageInsuredSchemeInsurance(models.Model):
    _name = 'wage.insured.scheme.insurance'
    _description = "参保险种"
    _rec_name = 'name'
    _order = 'id'

    active = fields.Boolean(string=u'Active', default=True)
    sequence = fields.Integer(string=u'序号')
    name = fields.Char(string='险种名称', required=True)
    base_number = fields.Float(string=u'险种基数', digits=(10, 2))
    company_number = fields.Float(string=u'公司比例', digits=(10, 4))
    personal_number = fields.Float(string=u'个人比例', digits=(10, 4))


class WageInsuredScheme(models.Model):
    _description = '参保方案'
    _name = 'wage.insured.scheme'
    _rec_name = 'name'
    _order = 'id'

    @api.model
    def _get_default_country_id(self):
        return self.env['res.company']._company_default_get('payment.transaction').country_id.id

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char(string='方案名称', required=True)
    country_id = fields.Many2one(comodel_name='res.country', string=u'国家', default=_get_default_country_id)
    country_state_id = fields.Many2one(comodel_name='res.country.state', string=u'参保城市',
                                       index=True, domain="[('country_id', '=?', country_id)]")
    line_ids = fields.One2many('wage.insured.scheme.line', inverse_name='scheme_id', string=u'参保险种')
    notes = fields.Text(string=u'备注')

    def create_all_insurance(self):
        """
        把所有的险种信息拉取到列表中
        :return:
        """
        for res in self:
            insurances = self.env['wage.insured.scheme.insurance'].search([])
            line_list = list()
            for insurance in insurances:
                line_list.append({
                    'insurance_id': insurance.id,
                    'base_number': insurance.base_number,
                    'company_number': insurance.company_number,
                    'personal_number': insurance.personal_number,
                })
            res.line_ids = line_list

    @api.onchange('name')
    @api.constrains('name')
    def _pull_all_insurance(self):
        for res in self:
            if len(res.line_ids) < 1:
                self.create_all_insurance()


class WageInsuredSchemeLine(models.Model):
    _description = '参保方案列表'
    _name = 'wage.insured.scheme.line'
    _rec_name = 'scheme_id'
    _order = 'id'

    sequence = fields.Integer(string=u'序号')
    scheme_id = fields.Many2one(comodel_name='wage.insured.scheme', string=u'参保方案')
    insurance_id = fields.Many2one(comodel_name='wage.insured.scheme.insurance', string=u'险种', required=True)
    base_number = fields.Float(string=u'险种基数', digits=(10, 2))
    company_number = fields.Float(string=u'公司比例', digits=(10, 4))
    personal_number = fields.Float(string=u'个人比例', digits=(10, 4))

    @api.onchange('insurance_id')
    def _onchange_insurance_id(self):
        """
        动态获取险种参数
        :return:
        """
        for res in self:
            if res.insurance_id:
                res.base_number = res.insurance_id.base_number
                res.company_number = res.insurance_id.company_number
                res.personal_number = res.insurance_id.personal_number
