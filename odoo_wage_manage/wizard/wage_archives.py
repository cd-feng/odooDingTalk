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


class WageArchivesTransient(models.TransientModel):
    _name = 'wage.archives.transient'
    _description = "批量初始化档案"

    @api.model
    def _get_default_line(self):
        structures = self.env['wage.structure'].search([])
        line_list = list()
        for structure in structures:
            line_list.append({
                'structure_id': structure.id,
                'wage_amount': 0,
            })
        return line_list

    emp_ids = fields.Many2many('hr.employee', string=u'员工')
    all_emp = fields.Boolean(string=u'全部员工?')
    get_info_by_hrm = fields.Boolean(string=u'同步花名册员工信息?')
    line_ids = fields.One2many(comodel_name='wage.archives.transient.line', inverse_name='transient_id', string=u'明细',
                               default=_get_default_line)

    def create_employee_archives(self):
        """
        批量初始化档案
        :return:
        """
        self.ensure_one()
        line_list = list()
        for line in self.line_ids:
            line_list.append((0, 0, {
                'structure_id': line.structure_id.id,
                'wage_amount': line.wage_amount,
            }))
        # 遍历所选员工
        # for emp in self.emp_ids.with_progress(msg="批量初始化档案"):
        for emp in self.emp_ids:
            logging.info(">>>生成员工：'%s' 档案" % emp.name)
            archives_data = {
                'employee_id': emp.id,
                'department_id': emp.department_id.id,
                'job_id': emp.job_id.id,
                'line_ids': line_list,
            }
            # 是否从花名册更新
            if self.get_info_by_hrm:
                archives_data = self.get_info_by_dingding_hrm(archives_data, emp)
            archives = self.env['wage.archives'].search([('employee_id', '=', emp.id)])
            if not archives:
                self.env['wage.archives'].create(archives_data)
            else:
                archives.write({'line_ids': [(2, archives.line_ids.ids)]})
                archives.write(archives_data)
        logging.info(">>>End批量初始化档案")
        action = self.env.ref('odoo_wage_manage.wage_archives_action')
        return action.read()[0]

    @api.model
    def get_info_by_dingding_hrm(self, archives_data, emp):
        """
        从钉钉花名册中获取员工信息
        :return:
        """
        roster = self.env['dingding.employee.roster'].sudo().search([('emp_id', '=', emp.id)], limit=1)
        if not roster:
            return archives_data
        archives_data.update({
            'department_id': roster.mainDept.id,
            'employee_code': roster.jobNumber,
            'job_id': roster.position.id,
            'bank_account_number': roster.bankAccountNo,
            'accountBank': roster.accountBank,
        })
        # 搜索发薪公司
        if roster.contractCompanyName:
            wac = self.env['wage.archives.company'].search([('name', '=', roster.contractCompanyName)], limit=1)
            if not wac:
                wac = self.env['wage.archives.company'].create({'name': roster.contractCompanyName})
            archives_data.update({
                'payroll_company': wac.id,
            })
        # 搜索户籍性质
        if roster.residenceType:
            whr = self.env['wage.household.registration'].search([('name', '=', roster.residenceType)], limit=1)
            if not whr:
                whr = self.env['wage.household.registration'].create({'name': roster.residenceType})
            archives_data.update({
                'household_id': whr.id,
            })
        return archives_data

    @api.onchange('all_emp')
    def onchange_all_emp(self):
        """
        获取全部员工
        :return:
        """
        if self.all_emp:
            employees = self.env['hr.employee'].search([])
            self.emp_ids = [(6, 0, employees.ids)]
        else:
            self.emp_ids = [(2, 0, self.emp_ids)]


class WageArchivesTransientLine(models.TransientModel):
    _description = '薪资结构'
    _name = 'wage.archives.transient.line'

    transient_id = fields.Many2one(comodel_name='wage.archives.transient', string=u'薪资档案')
    structure_id = fields.Many2one(comodel_name='wage.structure', string=u'薪资项目')
    wage_amount = fields.Float(string=u'薪资金额', digits=(10, 2))
