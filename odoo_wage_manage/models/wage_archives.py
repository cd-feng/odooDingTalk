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


class EmployeeWageArchives(models.Model):
    _description = '薪资档案'
    _name = 'wage.archives'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean('Active', default=True)
    code = fields.Char(string=u'档案编号', default='New', index=True)
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id, index=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', index=True, track_visibility='onchange')
    employee_code = fields.Char(string='员工工号')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True)
    job_id = fields.Many2one(comodel_name='hr.job', string=u'工作岗位')
    base_wage = fields.Float(string='基本工资', track_visibility='onchange')
    payroll_company = fields.Many2one(comodel_name='wage.archives.company', string=u'发薪公司', index=True)
    household_id = fields.Many2one(comodel_name='wage.household.registration', string=u'户籍性质', index=True)
    bank_account_number = fields.Char(string='银行卡号')
    accountBank = fields.Char(string='开户行')
    line_ids = fields.One2many(comodel_name='wage.archives.line', inverse_name='archives_id', string=u'薪资结构')
    notes = fields.Text(string=u'备注')

    @api.model
    def create(self, values):
        """
        创建时触发
        :param values:
        :return:
        """
        if not values.get('code') or values.get('code') == 'New':
            values.update({'code': self.env['ir.sequence'].sudo().next_by_code('wage.employee.archives.code')})
        return super(EmployeeWageArchives, self).create(values)

    @api.multi
    def create_all_structure(self):
        """
        初始化所有薪资结构
        :return:
        """
        for res in self:
            structures = self.env['wage.structure'].search([])
            line_list = list()
            for structure in structures:
                line_list.append({
                    'structure_id': structure.id,
                    'wage_amount': 0,
                })
            res.line_ids = line_list

    @api.onchange('employee_id')
    @api.constrains('employee_id')
    def _pull_all_structure(self):
        for res in self:
            if len(res.line_ids) < 1:
                self.create_all_structure()

    @api.multi
    def get_info_by_dingding_hrm(self):
        """
        从钉钉花名册中获取员工信息
        :return:
        """
        for res in self:
            roster = self.env['dingding.employee.roster'].search([('emp_id', '=', res.employee_id.id)], limit=1)
            if not roster:
                raise UserError("没有在钉钉花名册中发现该员工信息，请确保花名册为最新！")
            res.department_id = roster.mainDept.id
            res.employee_code = roster.jobNumber
            res.job_id = roster.position.id
            # 搜索发薪公司
            if roster.contractCompanyName:
                wac = self.env['wage.archives.company'].search([('name', '=', roster.contractCompanyName)], limit=1)
                if not wac:
                    wac = self.env['wage.archives.company'].create({'name': roster.contractCompanyName})
                res.payroll_company = wac.id
            # 搜索户籍性质
            if roster.residenceType:
                whr = self.env['wage.household.registration'].search([('name', '=', roster.residenceType)], limit=1)
                if not whr:
                    whr = self.env['wage.household.registration'].create({'name': roster.residenceType})
                res.household_id = whr.id
            res.bank_account_number = roster.bankAccountNo
            res.accountBank = roster.accountBank


class EmployeeWageArchivesLine(models.Model):
    _description = '薪资结构'
    _name = 'wage.archives.line'

    sequence = fields.Integer(string=u'序号')
    archives_id = fields.Many2one(comodel_name='wage.archives', string=u'薪资档案')
    structure_id = fields.Many2one(comodel_name='wage.structure', string=u'薪资项目')
    wage_amount = fields.Float(string=u'薪资金额', digits=(10, 2))

