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

WorkType = [
    ('00', '正常出勤'),
    ('01', '周末加班'),
    ('02', '法假加班'),
    ('03', '事假'),
]

user_status_choice = [('0', '未审核'), ('1', '已审核'), ('2', '已失效'), ]
status_choice = [('0', '未使用'), ('1', '使用中'), ('2', '已失效'), ]

EditAttendanceType = [
    ('00', '基本工资/应出勤天数/8*请假小时'),
    ('01', '基本工资/应出勤天数*请假小时'),
    ('02', '(按次数) 次数*每次事假扣款'),
]

rate_choice = [('0', '年'), ('1', '月')]

TimeResult = [
    ('Normal', '正常'),
    ('Early', '早退'),
    ('Late', '迟到'),
    ('SeriousLate', '严重迟到'),
    ('Absenteeism', '旷工迟到'),
    ('NotSigned', '未打卡'),
]
LocationResult = [
    ('Normal', '范围内'), ('Outside', '范围外'), ('NotSigned', '未打卡'),
]
SourceType = [
    ('ATM', '考勤机'),
    ('BEACON', 'IBeacon'),
    ('DING_ATM', '钉钉考勤机'),
    ('USER', '手机打卡'),
    ('BOSS', '管理员改签'),
    ('APPROVE', '审批系统'),
    ('SYSTEM', '考勤系统'),
    ('AUTO_CHECK', '自动打卡'),
    ('odoo', 'Odoo系统'),
]


# class LeaveInfo(models.Model):
#     _description = '假期信息表'
#     _name = 'leave.info'
#     _rec_name = 'emp_id'

#     emp_id = fields.Mnay2one('hr.employee', string='员工')
#     start_date = fields.Date('开始日期')
#     leave_info_time_start = fields.Datetime('请假开始时间')
#     end_date = fields.Date('结束日期')
#     leave_info_time_end = fields.Datetime('请假结束时间')
#     # leave_type = fields.Many2one('leave.type', string='假期类型')
#     leave_info_status = fields.Char('假期单据状态', selection=user_status_choice)


# class LeaveDetail(models.Model):
#     _description = '假期明细表'
#     _name = 'leave.detail'
#     _rec_name = 'leave_info_id'

#     emp_id = fields.Mnay2one('hr.employee.info', string='员工')
#     leave_info_id = fields.Many2one('leave.info', string='单据主键')
#     leave_date = fields.Date('请假日期')
#     leave_detail_time_start = fields.Datetime('请假开始时间', null=True, blank=True)
#     leave_detail_time_end = fields.Datetime('请假结束时间', null=True, blank=True)
#     # leave_type = fields.Many2one('leave.type', string='假期类型')
#     leave_info_status = fields.Char('假期明细单据状态', selection=status_choice)
#     count_length = fields.Float('长度统计')


class LegalHoliday(models.Model):
    _description = '法定节假日'
    _name = 'legal.holiday'
    _rec_name = 'legal_holiday_name'

    legal_holiday_name = fields.Char('法定节假日名称')
    legal_holiday = fields.Date('法定节假日')
    status = fields.Char('法定节假日状态', selection=status_choice)


class AttendanceInfo(models.Model):
    _description = '考勤日报表'
    _name = 'attendance.info'
    _inherit = 'hr.attendance'

    # @api.model
    # def _get_default_company(self):
    #     return self.env.user.company_id

    # company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    ding_group_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'钉钉考勤组')
    workDate = fields.Date(string=u'工作日')
    on_timeResult = fields.Selection(string=u'上班考勤结果', selection=TimeResult)
    off_timeResult = fields.Selection(string=u'下班考勤结果', selection=TimeResult)
    on_planId = fields.Char(string=u'上班班次ID')
    off_planId = fields.Char(string=u'下班班次ID')
    on_sourceType = fields.Selection(string=u'上班数据来源', selection=SourceType)
    off_sourceType = fields.Selection(string=u'下班数据来源', selection=SourceType)
    on_approveId = fields.Char(string='上班打卡关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    on_procInstId = fields.Char(string='上班打卡审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    off_approveId = fields.Char(string='下班打卡关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    off_procInstId = fields.Char(string='下班打卡审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    on_baseCheckTime = fields.Datetime(string=u'上班基准时间', help="计算迟到和早退，基准时间")
    off_baseCheckTime = fields.Datetime(string=u'下班基准时间', help="计算迟到和早退，基准时间")
    base_work_hours = fields.Float(string='应出勤小时', compute='_compute_base_work_hours', store=True, readonly=True)
    leave_hours = fields.Float(string='请假时长')
    attendance_date_status = fields.Selection(string=u'出勤性质', selection=WorkType, default='00')

    @api.depends('on_baseCheckTime', 'off_baseCheckTime')
    def _compute_base_work_hours(self):
        for attendance in self:
            if attendance.off_baseCheckTime:
                delta = attendance.off_baseCheckTime - attendance.on_baseCheckTime
                attendance.base_work_hours = delta.total_seconds() / 3600.0

    @api.model_create_multi
    def create(self, vals_list):
        """
        支持批量新建考勤记录
        :return:
        """
        return super(AttendanceInfo, self).create(vals_list)


class WageEmpAttendanceAnnal(models.Model):
    _description = '员工考勤统计'
    _name = 'wage.employee.attendance.annal'
    _rec_name = 'employee_id'
    _order = 'id'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.model
    def _get_default_date(self):
        return str(fields.date.today())

    company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True, track_visibility='onchange')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True, track_visibility='onchange')
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
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True, track_visibility='onchange')
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
            res_count = self.search_count([('employee_id', '=', res.employee_id.id), ('performance_code', '=', res.performance_code)])
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
    
    
