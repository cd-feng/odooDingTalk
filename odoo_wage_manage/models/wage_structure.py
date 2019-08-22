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


class WageAttendDaysConfig(models.Model):
    _description = '应出勤天数'
    _name = 'wage.attend.days.config'
    _rec_name = 'year'
    _order = 'year'

    year = fields.Char(string='年度', help="4为年份字符，如：2019")
    month_1 = fields.Integer(string=u'1月应出勤天数')
    month_2 = fields.Integer(string=u'2月应出勤天数')
    month_3 = fields.Integer(string=u'3月应出勤天数')
    month_4 = fields.Integer(string=u'4月应出勤天数')
    month_5 = fields.Integer(string=u'5月应出勤天数')
    month_6 = fields.Integer(string=u'6月应出勤天数')
    month_7 = fields.Integer(string=u'7月应出勤天数')
    month_8 = fields.Integer(string=u'8月应出勤天数')
    month_9 = fields.Integer(string=u'9月应出勤天数')
    month_10 = fields.Integer(string=u'10月应出勤天数')
    month_11 = fields.Integer(string=u'11月应出勤天数')
    month_12 = fields.Integer(string=u'12月应出勤天数')

    _sql_constraints = [('year_uniq', 'unique (year)', "年份已存在!!")]

    @api.model
    def get_month_attend_day(self, year_code, month):
        """
        返回该月应出勤天数
        :param year_code:
        :param month:
        :return:
        """
        attend = self.search([('year', '=', year_code)], limit=1)
        if not attend:
            raise UserError("年度'%s'未配置应出勤天数！" % year_code)
        if month == '01':
            return attend.month_1
        elif month == '02':
            return attend.month_2
        elif month == '03':
            return attend.month_3
        elif month == '04':
            return attend.month_4
        elif month == '05':
            return attend.month_5
        elif month == '06':
            return attend.month_6
        elif month == '07':
            return attend.month_7
        elif month == '08':
            return attend.month_8
        elif month == '09':
            return attend.month_9
        elif month == '10':
            return attend.month_10
        elif month == '11':
            return attend.month_11
        elif month == '12':
            return attend.month_12
        else:
            return 0


class WagePerformance(models.Model):
    _description = '绩效项目'
    _name = 'wage.performance.list'

    name = fields.Char(string='绩效项目名称', help="绩效项目名称")
    code = fields.Char(string='识别码')

    _sql_constraints = [('year_uniq', 'unique (year)', "年份已存在!!")]