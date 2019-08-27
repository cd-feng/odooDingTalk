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


class WagePayrollAccounting(models.Model):
    _description = '薪资核算'
    _name = 'wage.payroll.accounting'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='名称')
    wage_date = fields.Date(string=u'核算月份', required=True)
    date_code = fields.Char(string='期间代码', index=True)
    company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True)
    job_id = fields.Many2one(comodel_name='hr.job', string=u'在职岗位', index=True)
    employee_code = fields.Char(string='员工工号')
    # 基本+缺勤
    base_wage = fields.Float(string='基本工资', track_visibility='onchange', digits=(10, 2))
    structure_ids = fields.One2many('wage.payroll.accounting.structure', 'accounting_id', string=u'薪资项目')
    attendance_days = fields.Float(string=u'应出勤天数', digits=(10, 2))
    leave_absence = fields.Float(string=u'事假扣款', digits=(10, 2))
    sick_absence = fields.Float(string=u'病假扣款', digits=(10, 2))
    absence_sum = fields.Float(string=u'缺勤扣款合计', digits=(10, 2), compute='_compute_amount_sum')
    # 绩效
    performance_ids = fields.One2many('wage.payroll.accounting.performance.line', 'accounting_id', string=u'绩效列表')
    performance_sum = fields.Float(string=u'绩效合计', digits=(10, 2), compute='_compute_amount_sum')
    # 加班
    work_overtime = fields.Float(string=u'工作日加班费', digits=(10, 2))
    weekend_overtime = fields.Float(string=u'周末加班费', digits=(10, 2))
    holiday_overtime = fields.Float(string=u'节假日加班费', digits=(10, 2))
    overtime_sum = fields.Float(string=u'加班费合计', digits=(10, 2), compute='_compute_amount_sum')
    # 打卡
    late_attendance = fields.Float(string=u'迟到扣款', digits=(10, 2))
    notsigned_attendance = fields.Float(string=u'忘记打卡扣款', digits=(10, 2))
    early_attendance = fields.Float(string=u'早退扣款', digits=(10, 2))
    attendance_sum = fields.Float(string=u'打卡扣款合计', digits=(10, 2), compute='_compute_amount_sum')
    # 社保公积金
    statement_ids = fields.One2many('wage.payroll.accounting.monthly.statement.line', 'accounting_id', string=u'社保公积金')
    # 个税
    cumulative_expenditure_deduction = fields.Float(string=u'累计子女教育抵扣总额', digits=(10, 2))
    cumulative_home_loan_interest_deduction = fields.Float(string=u'累计住房贷款利息抵扣总额', digits=(10, 2))
    cumulative_housing_rental_expense_deduction = fields.Float(string=u'累计住房租金抵扣总额', digits=(10, 2))
    cumulative_support_for_the_elderly = fields.Float(string=u'累计赡养老人抵扣总额', digits=(10, 2))
    cumulative_continuing_education_deduction = fields.Float(string=u'累计继续教育抵扣总额', digits=(10, 2))
    cumulative_total_tax_deduction = fields.Float(string=u'累计个税抵扣总额', digits=(10, 2))
    taxable_salary_this_month = fields.Float(string=u'本月计税工资', digits=(10, 2))
    cumulative_tax_pay = fields.Float(string=u'累计计税工资', digits=(10, 2))
    tax_rate = fields.Float(string=u'税率', digits=(10, 2))
    quick_deduction = fields.Float(string=u'速算扣除数', digits=(10, 2))
    this_months_tax = fields.Float(string=u'本月个税', digits=(10, 2))
    cumulative_tax = fields.Float(string=u'累计个税', digits=(10, 2))
    # 小计
    pay_wage = fields.Float(string=u'应发工资', digits=(10, 2))
    real_wage = fields.Float(string=u'实发工资', digits=(10, 2))
    notes = fields.Text(string=u'备注')

    @api.onchange('wage_date')
    @api.constrains('wage_date')
    def _alter_date_code(self):
        """
        根据日期生成期间代码
        :return:
        """
        for res in self:
            if res.wage_date:
                wage_date = str(res.wage_date)
                res.date_code = "{}/{}".format(wage_date[:4], wage_date[5:7])

    @api.constrains('employee_id', 'date_code')
    def _constranint_employee(self):
        """
        检查员工同一期间是否存在多条记录
        :return:
        """
        for res in self:
            count_num = self.search_count([('employee_id', '=', res.employee_id.id), ('date_code', '=', res.date_code)])
            if count_num > 1:
                raise UserError("员工{}在{}期间已存在数据，请勿重复创建!".format(res.employee_id.name, res.date_code))

    @api.constrains('employee_id', 'wage_date')
    def _constrains_name(self):
        """
        生成name字段
        :return:
        """
        for res in self:
            if res.employee_id and res.wage_date:
                res.name = "{}&{}".format(res.employee_id.name, str(res.wage_date)[:7])

    def _compute_amount_sum(self):
        """
        计算合计项
        :return:
        """
        for res in self:
            # 缺勤扣款合计 = 事假扣款+病假扣款
            absence_sum = res.leave_absence + res.sick_absence
            # 绩效合计
            performance_sum = 0
            for performance in res.performance_ids:
                performance_sum += performance.wage_amount
            # 加班费合计 = 工作日加班费+周末加班费+节假日加班费
            overtime_sum = res.work_overtime + res.weekend_overtime + res.holiday_overtime
            # 打卡扣款合计 = 迟到扣款+忘记打卡扣款+早退扣款
            attendance_sum = res.late_attendance + res.notsigned_attendance + res.early_attendance
            res.update({
                'absence_sum': absence_sum,
                'performance_sum': performance_sum,
                'overtime_sum': overtime_sum,
                'attendance_sum': attendance_sum,
            })


class WagePayrollAccountingLine(models.Model):
    _description = '薪资项目'
    _name = 'wage.payroll.accounting.structure'

    sequence = fields.Integer(string=u'序号')
    accounting_id = fields.Many2one(comodel_name='wage.payroll.accounting', string=u'薪资档案')
    structure_id = fields.Many2one(comodel_name='wage.structure', string=u'薪资项目')
    wage_amount = fields.Float(string=u'薪资金额', digits=(10, 2))


class WagePayrollAccountingPerformanceLine(models.Model):
    _name = 'wage.payroll.accounting.performance.line'
    _description = "绩效统计列表"

    name = fields.Char(string='说明')
    sequence = fields.Integer(string=u'序号')
    accounting_id = fields.Many2one(comodel_name='wage.payroll.accounting', string=u'薪资核算')
    performance_id = fields.Many2one(comodel_name='wage.performance.list', string=u'绩效项目')
    wage_amount = fields.Float(string=u'绩效金额')


class WagePayrollMonthlyStatementLine(models.Model):
    _description = '社保公积金列表'
    _name = 'wage.payroll.accounting.monthly.statement.line'

    sequence = fields.Integer(string=u'序号')
    accounting_id = fields.Many2one(comodel_name='wage.payroll.accounting', string=u'薪资核算')
    insurance_id = fields.Many2one(comodel_name='wage.insured.scheme.insurance', string=u'险种', required=True)
    base_number = fields.Float(string=u'险种基数', digits=(10, 2))
    company_pay = fields.Float(string=u'公司缴纳', digits=(10, 4))
    pension_pay = fields.Float(string=u'个人缴纳', digits=(10, 4))


