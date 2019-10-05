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
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LegalHoliday(models.Model):
    _description = '法定节假日'
    _name = 'legal.holiday'
    _rec_name = 'legal_holiday_name'

    legal_holiday_name = fields.Char('法定节假日名称')
    legal_holiday = fields.Date('法定节假日')
    status = fields.Char('法定节假日状态', selection=[('0', '未使用'), ('1', '使用中'), ('2', '已失效')])


class WageEmpAttendanceAnnal(models.Model):
    _description = '员工考勤统计'
    _name = 'wage.employee.attendance.annal'
    _rec_name = 'employee_id'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.model
    def _get_default_date(self):
        return str(fields.date.today())

    company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True, track_visibility='onchange')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工',
                                  required=True, index=True, track_visibility='onchange')
    job_id = fields.Many2one(comodel_name='hr.job', string=u'在职岗位')
    employee_number = fields.Char(string='员工工号')
    attendance_month = fields.Date(string=u'考勤日期', required=True, index=True, default=_get_default_date)
    attend_code = fields.Char(string='考勤期间', index=True)
    # 加班
    work_overtime_hour = fields.Float(string=u'工作日加班(小时)', digits=(10, 1))
    weekend_overtime_hour = fields.Float(string=u'周末加班(小时)', digits=(10, 1))
    holiday_overtime_hour = fields.Float(string=u'节假日加班(小时)', digits=(10, 1),)
    # 缺勤
    leave_absence_hour = fields.Float(string=u'事假缺勤(小时)', digits=(10, 1))
    sick_absence_hour = fields.Float(string=u'病假缺勤(小时)', digits=(10, 1))
    # 打卡
    late_attendance_num = fields.Integer(string=u'迟到次数')
    notsigned_attendance_num = fields.Integer(string=u'忘记打卡次数')
    early_attendance_num = fields.Integer(string=u'早退次数')

    arrive_total = fields.Float('应到天数')
    real_arrive_total = fields.Float('实到天数')
    absenteeism_total = fields.Float('旷工天数')
    late_total = fields.Float('迟到/早退次数')
    sick_leave_total = fields.Float('病假天数')
    personal_leave_total = fields.Float('事假天数')
    annual_leave_total = fields.Float('年假天数')
    marriage_leave_total = fields.Float('婚假天数')
    bereavement_leave_total = fields.Float('丧假天数')
    paternity_leave_total = fields.Float('陪产假天数')
    maternity_leave_total = fields.Float('产假天数')
    work_related_injury_leave_total = fields.Float('工伤假天数')
    home_leave_total = fields.Float('探亲假天数')
    travelling_total = fields.Float('出差天数')
    other_leave_total = fields.Float('其他假天数')

    @api.constrains('attendance_month')
    @api.onchange('attendance_month')
    def _constrains_attendance_month(self):
        for res in self:
            if res.attendance_month:
                month_date = str(res.attendance_month)
                res.attend_code = "{}/{}".format(month_date[:4], month_date[5:7])

    @api.constrains('employee_id')
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for res in self:
            if res.employee_id:
                res.job_id = res.employee_id.job_id.id
                res.department_id = res.employee_id.department_id.id
                res.employee_number = res.employee_id.din_jobnumber


class WageEmployeePerformance(models.Model):
    _name = 'wage.employee.performance.manage'
    _description = "员工绩效统计"
    _order = 'id'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.model
    def _get_default_date(self):
        return str(fields.date.today())

    company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True, track_visibility='onchange')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工',
                                  required=True, index=True, track_visibility='onchange')
    job_id = fields.Many2one(comodel_name='hr.job', string=u'在职岗位')
    employee_number = fields.Char(string='员工工号')
    performance_month = fields.Date(string=u'绩效日期', required=True, index=True, default=_get_default_date)
    performance_code = fields.Char(string='绩效期间', index=True)
    line_ids = fields.One2many('wage.employee.performance.manage.line', 'manage_id', string=u'绩效明细')

    performance_wage = fields.Float(string=u'绩效工资', digits=(10, 2))
    work_reward = fields.Float(string=u'工作奖励', digits=(10, 2))
    class_fee = fields.Float(string=u'课时费', digits=(10, 2))
    performance_bonus = fields.Float(string=u'业绩提成', digits=(10, 2))
    other_wage = fields.Float(string=u'其他', digits=(10, 2))
    notes = fields.Text(string=u'备注')

    @api.constrains('performance_month')
    @api.onchange('performance_month')
    def _constrains_performance_month(self):
        for res in self:
            if res.performance_month:
                month_date = str(res.performance_month)
                res.performance_code = "{}/{}".format(month_date[:4], month_date[5:7])
            res_count = self.search_count([('employee_id', '=', res.employee_id.id),
                                           ('performance_code', '=', res.performance_code)])
            if res_count > 1:
                raise UserError("员工：{}和绩效期间：{}已存在！".format(res.employee_id.name, res.performance_code))

    @api.constrains('employee_id')
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for res in self:
            if res.employee_id:
                res.job_id = res.employee_id.job_id.id
                res.department_id = res.employee_id.department_id.id
                res.employee_number = res.employee_id.din_jobnumber

    @api.multi
    def get_emp_performance_list(self):
        performance_list = list()
        amount_sum = 0
        for line in self.line_ids:
            performance_list.append((0, 0, {
                'performance_id': line.performance_id.id,
                'wage_amount': line.wage_amount,
                'name': line.name,
            }))
            amount_sum += line.wage_amount
        return performance_list, amount_sum


class WageEmployeePerformanceLine(models.Model):
    _name = 'wage.employee.performance.manage.line'
    _description = "员工绩效统计列表"

    name = fields.Char(string='说明')
    sequence = fields.Integer(string=u'序号')
    manage_id = fields.Many2one(comodel_name='wage.employee.performance.manage', string=u'绩效统计')
    performance_id = fields.Many2one(comodel_name='wage.performance.list', string=u'绩效项目')
    wage_amount = fields.Float(string=u'绩效金额')
