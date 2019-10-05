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
        # for emp in self.emp_ids.with_progress(msg="开始计算薪资"):
        for emp in self.emp_ids:
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
            base_wage = performance_amount_sum = structure_amount_sum = 0      # 基本工资,绩效合计,薪资结构合计金额
            structure_ids = list()
            performance_ids = list()
            statement_ids = list()
            if archives:
                # 读取薪资档案中员工薪资结构数据
                structure_ids, structure_amount_sum = archives.get_employee_wage_structure()
                base_wage = archives.get_employee_salary()
            # 获取绩效列表
            domain = [('employee_id', '=', emp.id), ('performance_code', '=', date_code)]
            performance = self.env['wage.employee.performance.manage'].search(domain, limit=1)
            if performance:
                performance_ids, performance_amount_sum = performance.get_emp_performance_list()
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
            absence_amount_sum = overtime_amount_sum = attendance_amount_sum = 0
            if attendance:
                # 计算事假
                leave_absence = rules.compute_leave_deduction(base_wage, attendance_days, attendance.leave_absence_hour)
                # 计算病假
                sick_absence = rules.compute_sick_absence(base_wage, attendance_days, attendance.sick_absence_hour)
                # 工作日加班费
                work_overtime = rules.compute_work_overtime(base_wage, attendance_days, attendance.work_overtime_hour)
                # 周末加班费
                weekend_overtime = rules.compute_weekend_overtime(
                    base_wage, attendance_days, attendance.weekend_overtime_hour)
                # 节假日加班费
                holiday_overtime = rules.compute_holiday_overtime(
                    base_wage, attendance_days, attendance.holiday_overtime_hour)
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
                absence_amount_sum = leave_absence + sick_absence
                overtime_amount_sum = work_overtime + weekend_overtime + holiday_overtime
                attendance_amount_sum = late_attendance + notsigned_attendance + early_attendance
            # 计算应发工资
            # 应发工资=基本工资+薪资结构+ 绩效合计-缺勤扣款合计+加班费合计-打卡扣款合计
            pay_wage = base_wage + structure_amount_sum + performance_amount_sum - \
                absence_amount_sum + overtime_amount_sum - attendance_amount_sum
            payroll_data.update({'pay_wage': pay_wage})
            payroll_data = self._compute_employee_tax(pay_wage, payroll_data, emp, date_code)
            # 判断是否已存在该期间的员工核算信息
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

    # 计算个税
    @api.model
    def _compute_employee_tax(self, pay_wage, payroll_data, emp, date_code):
        """
        :param pay_wage:应发工资
        :param payroll_data:
        :param emp:
        :param date_code:期间
        :return:
        """
        month_code = date_code[5:7]
        # 获取个税明细
        emp_tax = self.env['wage.employee.tax.details'].sudo().search(
            [('employee_id', '=', emp.id), ('year', '=', date_code[:4])], limit=1)
        if not emp_tax:
            raise UserError("员工'%s'不存在年度'%s'个税明细！请先创建或初始化..." % (emp.name, date_code[:4]))
        # 获取专项附加扣除
        domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
        deduction = self.env['wage.special.additional.deduction'].sudo().search(domain, limit=1)
        cumulative_expenditure_deduction = 0
        cumulative_support_for_the_elderly = 0
        cumulative_continuing_education_deduction = 0
        cumulative_home_loan_interest_deduction = 0
        cumulative_housing_rental_expense_deduction = 0
        if deduction:
            cumulative_expenditure_deduction = deduction.cumulative_expenditure_deduction
            cumulative_support_for_the_elderly = deduction.cumulative_support_for_the_elderly
            cumulative_continuing_education_deduction = deduction.cumulative_continuing_education_deduction
            cumulative_home_loan_interest_deduction = deduction.cumulative_home_loan_interest_deduction
            cumulative_housing_rental_expense_deduction = deduction.cumulative_housing_rental_expense_deduction
        # 累计个税抵扣总额
        total_tax_deduction = cumulative_expenditure_deduction + cumulative_support_for_the_elderly + cumulative_continuing_education_deduction + \
            cumulative_home_loan_interest_deduction + cumulative_housing_rental_expense_deduction
        cumulative_tax_pay = 0       # 累计计税工资
        exemption = 0                # 累计免征额
        cumulative_actual_tax = 0    # 累计实际个税
        lsy_tax_wage = 0             # 历史月份计税工资
        for line in emp_tax.line_ids:
            # 获取月份的前一个月
            if int(month_code) == 1:
                exemption = 5000
            elif int(month_code) - 1 == int(line.month):
                exemption += line.accumulated_exemption + 5000
                cumulative_tax_pay = line.cumulative_tax_pay + pay_wage
                cumulative_actual_tax = line.cumulative_actual_tax
            # 获取累计计税工资、累计实际个税
            if int(line.month) < int(month_code):
                lsy_tax_wage += line.taxable_salary_this_month
        # 累计应税工资 = 本月计税工资 + 历史月份计税工资 - 累计个税抵扣 - 累计免税额
        cumulative_tax = pay_wage + lsy_tax_wage - total_tax_deduction - exemption
        # 累计应扣个税 税率  速算扣除数
        accumulated_deductible_tax, tax, quick_deduction = self._compute_cumulative_tax_payable_by_number(
            cumulative_tax)
        # 本月个税 = 累计应扣个税 - 累计实际个税
        this_months_tax = accumulated_deductible_tax - cumulative_actual_tax
        # 创建该员工个税明细
        tax_data = {
            'month': month_code,
            'taxable_salary_this_month': pay_wage,
            'cumulative_tax_pay': cumulative_tax_pay,
            'cumulative_tax_deduction': total_tax_deduction,
            'accumulated_exemption': exemption,
            'cumulative_taxable_wage': cumulative_tax,
            'tax': tax,
            'quick_deduction': quick_deduction,
            'accumulated_deductible_tax': accumulated_deductible_tax,
            'this_months_tax': this_months_tax,
            'cumulative_actual_tax': accumulated_deductible_tax,
        }
        emp_tax.set_employee_tax_detail(month_code, tax_data)
        # 将个税明细封装到薪资核算data中
        payroll_data.update({
            'cumulative_expenditure_deduction': cumulative_expenditure_deduction,
            'cumulative_home_loan_interest_deduction': cumulative_home_loan_interest_deduction,
            'cumulative_housing_rental_expense_deduction': cumulative_housing_rental_expense_deduction,
            'cumulative_support_for_the_elderly': cumulative_support_for_the_elderly,
            'cumulative_continuing_education_deduction': cumulative_continuing_education_deduction,
            'cumulative_total_tax_deduction': total_tax_deduction,  # 累计个税抵扣总额
            'taxable_salary_this_month': pay_wage,   # 本月计税工资
            'cumulative_tax_pay': cumulative_tax_pay,   # 累计计税工资
            'tax_rate': tax,   # 税率
            'quick_deduction': quick_deduction,        # 速算扣除数
            'this_months_tax': this_months_tax,        # 本月个税
            'cumulative_tax': cumulative_tax,          # 累计个税
            'real_wage': pay_wage - this_months_tax,   # 实发工资
        })
        return payroll_data

    @api.model
    def _compute_cumulative_tax_payable_by_number(self, number):
        """
        根据"累计应税工资"计算 累计应纳税额
        居民工资、薪金个人所得税预扣预缴税率表
        级数	  累计应税工资（累计应税工资）			              预扣率（%）		速算扣除数
        1	  不超过36000元的部分							            3			0
        2	  超过36000元至144000元的部分							    10			2520
        3	  超过144000元至300000元的部分							20			16920
        4	  超过300000元至420000元的部分							25			31920
        5	  超过420000元至660000元的部分							30			52920
        6	  超过660000元至960000元的部分							35			85920
        7	  超过960000元的部分							            45			181920
        :param number: 累计应税工资
        :return: 累计应纳税额
        """
        result = 0.0
        tax = 0
        quick_deduction = 0
        if number <= 36000:
            result = number * 0.03 - 0
            tax = 0.03
            quick_deduction = 0
        elif 36000 < number <= 144000:
            result = number * 0.10 - 2520
            tax = 0.10
            quick_deduction = 2520
        elif 144000 < number <= 300000:
            result = number * 0.20 - 16920
            tax = 0.20
            quick_deduction = 16920
        elif 300000 < number <= 420000:
            result = number * 0.25 - 31920
            tax = 0.25
            quick_deduction = 31920
        elif 420000 < number <= 660000:
            result = number * 0.30 - 52920
            tax = 0.30
            quick_deduction = 52920
        elif 660000 < number <= 960000:
            result = number * 0.35 - 85920
            tax = 0.35
            quick_deduction = 85920
        elif number >= 960000:
            result = number * 0.45 - 181920
            tax = 0.45
            quick_deduction = 181920
        return result, tax, quick_deduction


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
        else:
            self.emp_ids = [(2, 0, self.emp_ids)]

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

    def create_employee_payslip(self):
        """
        生成工资条
        :return:
        """
        self.ensure_one()
        start_date = str(self.start_date)
        date_code = "{}/{}".format(start_date[:4], start_date[5:7])
        # for emp in self.emp_ids.with_progress(msg="开始生成工资条"):
        for emp in self.emp_ids:
            payroll_data = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'date_code': date_code,
                'employee_id': emp.id,
                'department_id': emp.department_id.id if emp.department_id else False,
                'job_id': emp.job_id.id if emp.job_id else False,
            }
            # 获取薪资核算明细
            domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
            payroll = self.env['wage.payroll.accounting'].search(domain, limit=1)
            if payroll:
                payroll_data.update({
                    'base_wage': payroll.base_wage,  # 基本工资
                    'structure_wage': 0,  # 薪资项目
                    'absence_sum': payroll.absence_sum,  # 缺勤扣款合计
                    'performance_sum': payroll.performance_sum,  # 绩效合计
                    'overtime_sum': payroll.overtime_sum,  # 加班费合计
                    'attendance_sum': payroll.attendance_sum,  # 打卡扣款合计
                    'this_months_tax': payroll.this_months_tax,  # 本月个税
                    'pay_wage': payroll.pay_wage,  # 应发工资
                    'real_wage': payroll.real_wage,  # 实发工资
                    'statement_sum': payroll.statement_sum,  # 社保个人合计
                    'structure_sum': payroll.structure_sum,  # 薪资项目合计
                })
            # 创建工资单
            domain = [('employee_id', '=', emp.id), ('date_code', '=', date_code)]
            payrolls = self.env['odoo.wage.payslip'].search(domain)
            if not payrolls:
                self.env['odoo.wage.payslip'].sudo().create(payroll_data)
            else:
                payrolls.sudo().write(payroll_data)
        action = self.env.ref('odoo_wage_manage.odoo_wage_payslip_action')
        return action.read()[0]


class SendPayrollAccountingToPayslipEmailTransient(models.TransientModel):
    _name = 'send.wage.payroll.to.email.transient'
    _description = "通过EMAIL发送核算明细至员工"

    wage_date = fields.Date(string=u'核算月份', required=True)
    date_code = fields.Char(string='期间代码')
    payroll_ids = fields.Many2many('wage.payroll.accounting',
                                   relation='payroll_accounting_email_wage_payroll_accounting_rel', string=u'核算明细')
    all_payroll = fields.Boolean(string=u'所有核算明细?')

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

    def send_email_now(self):
        """
        批量发送核算明细至员工email,注意不是立即发送，通过邮件：EMail队列管理器进行发送
        :return:
        """
        self.ensure_one()
        template_id = self.env.ref('odoo_wage_manage.wage_payroll_accounting_email_template', raise_if_not_found=False)
        if not template_id:
            return False
        wage_date = str(self.wage_date)
        date_code = "{}/{}".format(wage_date[:4], wage_date[5:7])
        payrolls = self.env['wage.payroll.accounting'].sudo().search([('date_code', '=', date_code)])
        # for payroll in payrolls.with_progress(msg="开始发送Emial"):
        for payroll in payrolls:
            if payroll.employee_id.work_email:
                logging.info("email至%s" % payroll.name)
                template_id.sudo().with_context(lang=self.env.context.get('lang')).send_mail(payroll.id, force_send=False)
                payroll.email_state = True
