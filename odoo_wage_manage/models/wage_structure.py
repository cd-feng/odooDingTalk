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


class WageStructure(models.Model):
    _name = 'wage.structure'
    _description = "薪资结构"
    _rec_name = 'name'
    _order = 'id'

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char(string='名称', required=True, index=True)


class WageArchivesCompany(models.Model):
    _description = '发薪公司'
    _name = 'wage.archives.company'
    _order = 'id'

    name = fields.Char(string='名称', required=True, index=True)
    code = fields.Char(string='编号')

    @api.constrains('name')
    def _constrains_company_name(self):
        """
        检查名称是否重复
        :return:
        """
        for res in self:
            result = self.search_count([('name', '=', res.name)])
            if result > 1:
                raise UserError("公司名称已存在！")


class WageHouseholdRegistration(models.Model):
    _description = '户籍性质'
    _name = 'wage.household.registration'
    _order = 'id'

    name = fields.Char(string='名称', required=True, index=True)
    code = fields.Char(string='编号')

    @api.constrains('name')
    def _constrains_household_name(self):
        """
        检查名称是否重复
        :return:
        """
        for res in self:
            result = self.search_count([('name', '=', res.name)])
            if result > 1:
                raise UserError("户籍性质名称已存在！")

