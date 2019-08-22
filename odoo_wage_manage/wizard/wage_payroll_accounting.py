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


class WagePayrollAccountingTransient(models.TransientModel):
    _name = 'wage.payroll.accounting.transient'
    _description = "薪资计算"

    wage_date = fields.Date(string=u'核算月份', required=True)
    date_code = fields.Char(string='期间代码')
    emp_ids = fields.Many2many('hr.employee', string=u'员工')
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

    @api.onchange('wage_date')
    def _alter_date_code(self):
        """
        根据日期生成期间代码
        :return:
        """
        for res in self:
            if res.wage_date:
                wage_date = str(res.wage_date)
                res.date_code = "{}/{}".format(wage_date[:4], wage_date[5:7])

    @api.multi
    def compute_payroll_accounting(self):
        """
        计算薪资
        :return:
        """
        self.ensure_one()
        wage_date = str(self.wage_date)
        date_code = "{}/{}".format(wage_date[:4], wage_date[5:7])
        # 获取应出勤天数
        attendance_days = self.env['wage.attend.days.config'].get_month_attend_day(date_code[:4], date_code[5:7])
        # 获取薪酬计算规则
        rules = self.env['wage.calculate.salary.rules'].search([], limit=1)
        if not rules:
            raise UserError("请先配置一个薪资计算规则！")
        for emp in self.emp_ids.with_progress(msg="开始计算薪资"):
            payroll_data = {
                'wage_date': self.wage_date,
                'date_code': date_code,
                'employee_id': emp.id,
                'department_id': emp.department_id.id if emp.department_id else False,
                'job_id': emp.job_id.id if emp.job_id else False,
                'attendance_days': attendance_days,
            }
            # 获取员工薪资合同
            archives = self.env['wage.archives'].search([('employee_id', '=', emp.id)], limit=1)
            base_wage = 0
            structure_ids = list()
            performance_ids = list()
            statement_ids = list()
            if archives:
                # 读取薪资档案中员工薪资结构数据
                structure_ids = archives.get_employee_wage_structure()
                base_wage = archives.base_wage
            # 获取绩效列表
            domain = [('employee_id', '=', emp.id), ('performance_code', '=', date_code)]
            performance = self.env['wage.employee.performance.manage'].search(domain, limit=1)
            if performance:
                performance_ids = performance.get_emp_performance_list()
            # 获取社保月结账单
            domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
            statements = self.env['wage.insured.monthly.statement'].search(domain, limit=1)
            if statements:
                statement_ids = statements.get_employee_monthly_statement_line()
            payroll_data.update({
                'base_wage': base_wage,  # 基本工资
                'structure_ids': structure_ids,  # 薪资结构
                'performance_ids': performance_ids,   # 绩效列表
                'statement_ids': statement_ids,   # 社保公积金
            })
            # 获取员工考勤统计表
            domain = [('employee_id', '=', emp.id), ('attend_code', '=', date_code)]
            attendance = self.env['wage.employee.attendance.annal'].search(domain, limit=1)
            if attendance:
                # 计算事假
                leave_absence = rules.compute_leave_deduction(base_wage, attendance_days, attendance.leave_absence_hour)
                # 计算病假
                sick_absence = rules.compute_sick_absence(base_wage, attendance_days, attendance.sick_absence_hour)
                # 工作日加班费
                work_overtime = rules.compute_work_overtime(base_wage, attendance_days, attendance.work_overtime_hour)
                # 周末加班费
                weekend_overtime = rules.compute_weekend_overtime(base_wage, attendance_days, attendance.weekend_overtime_hour)
                # 节假日加班费
                holiday_overtime = rules.compute_holiday_overtime(base_wage, attendance_days, attendance.holiday_overtime_hour)
                # 迟到扣款
                late_attendance = rules.compute_late_attendance(attendance.late_attendance_num)
                # 忘记打卡扣款
                notsigned_attendance = rules.compute_notsigned_attendance(attendance.notsigned_attendance_num)
                # 早退扣款
                early_attendance = rules.compute_early_attendance(attendance.early_attendance_num)
                payroll_data.update({
                    'leave_absence': leave_absence,
                    'sick_absence': sick_absence,
                    'work_overtime': work_overtime,
                    'weekend_overtime': weekend_overtime,
                    'holiday_overtime': holiday_overtime,
                    'late_attendance': late_attendance,
                    'notsigned_attendance': notsigned_attendance,
                    'early_attendance': early_attendance,
                })

            domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
            payrolls = self.env['wage.payroll.accounting'].search(domain)
            if not payrolls:
                self.env['wage.payroll.accounting'].create(payroll_data)
            else:
                payrolls.write({
                    'structure_ids': [(2, payrolls.structure_ids.ids)],
                    'performance_ids': [(2, payrolls.performance_ids.ids)],
                    'statement_ids': [(2, payrolls.statement_ids.ids)],
                })
                payrolls.write(payroll_data)
        action = self.env.ref('odoo_wage_manage.wage_payroll_accounting_action')
        return action.read()[0]


class PayrollAccountingToPayslipTransient(models.TransientModel):
    _name = 'wage.payroll.accounting.to.payslip.transient'
    _description = "生成工资条"

    start_date = fields.Date(string=u'所属期起', required=True)
    end_date = fields.Date(string=u'所属期止', required=True)
    date_code = fields.Char(string='期间')
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
        根据日期生成期间代码
        :return:
        """
        for res in self:
            if res.start_date:
                start_date = str(res.start_date)
                res.date_code = "{}/{}".format(start_date[:4], start_date[5:7])

    @api.multi
    def create_employee_payslip(self):
        """
        生成工资条
        :return:
        """
        self.ensure_one()
        start_date = str(self.start_date)
        date_code = "{}/{}".format(start_date[:4], start_date[5:7])
        for emp in self.emp_ids.with_progress(msg="开始生成工资条"):
            payroll_data = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'date_code': date_code,
                'employee_id': emp.id,
                'department_id': emp.department_id.id if emp.department_id else False,
                'job_id': emp.job_id.id if emp.job_id else False,
            }
            domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
            payrolls = self.env['odoo.wage.payslip'].search(domain)
            if not payrolls:
                self.env['odoo.wage.payslip'].create(payroll_data)
            else:
                payrolls.write(payroll_data)
        action = self.env.ref('odoo_wage_manage.odoo_wage_payslip_action')
        return action.read()[0]
