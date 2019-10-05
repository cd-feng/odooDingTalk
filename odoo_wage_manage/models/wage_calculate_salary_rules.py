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


class WageCalculateSalaryRules(models.Model):
    _description = '计薪规则'
    _name = 'wage.calculate.salary.rules'
    _rec_name = 'name'

    name = fields.Char(string='规则名称')
    notes = fields.Text(string=u'备注')
    PLSELECTION = [('dingding', '从钉钉花名册提取'), ('odoo', '从Odoo员工提取')]
    personnel_information = fields.Selection(string=u'人事信息', selection=PLSELECTION, default='dingding')
    FIXEDSELECTION = [
        ('00', '基本工资'),
        ('01', '基本工资+薪资档案(薪资项目金额总和)'),
    ]
    fixed_salary = fields.Selection(string=u'固定工资', selection=FIXEDSELECTION, default='01')
    PERFORMANCESELECTION = [('import', '每月手动导入')]
    performance_bonus = fields.Selection(string=u'绩效奖金', selection=PERFORMANCESELECTION, default='import')

    leave_selection = [
        ('00', '基本工资/应出勤天数/8*请假小时'),
        ('01', '基本工资/应出勤天数*请假小时'),
        ('02', '(按次数) 次数*每次事假扣款'),
    ]

    leave_deduction = fields.Selection(string=u'事假扣款规则', selection=leave_selection, default='00')
    hour_leave_number = fields.Integer(string=u'多少小时算1次事假')
    leave_money = fields.Float(string=u'每次事假扣款', digits=(10, 2))

    sick_selection = [
        ('00', '基本工资/2/应出勤天数/8*请假小时'),
        ('01', '基本工资/应出勤天数*请假小时*病假扣款比例'),
        ('02', '基本工资/应出勤天数*请假小时/8*病假扣款比例'),
        ('03', '(按次数) 次数*每次病假扣款'),
    ]
    sick_deduction = fields.Selection(string=u'病假扣款规则', selection=sick_selection, default='00')
    hour_sick_number = fields.Integer(string=u'多少小时算1次病假')
    sick_money = fields.Float(string=u'每次病假扣款', digits=(10, 2))
    sick_deduction_ratio = fields.Float(string=u'病假扣款比例', digits=(10, 2))

    work_overtime_selection = [
        ('00', '基本工资/应出勤天数/8*加班小时*倍数'),
        ('01', '加班小时*固定金额'),
    ]
    work_overtime_deduction = fields.Selection(string=u'工作日加班规则', selection=work_overtime_selection, default='00')
    work_overtime_money = fields.Float(string=u'固定金额', digits=(10, 2))
    work_overtime_multiple = fields.Float(string=u'倍数', digits=(10, 1))

    weekend_selection = [
        ('00', '基本工资/应出勤天数/8*加班小时*倍数'),
        ('01', '加班小时*固定金额'),
    ]
    weekend_deduction = fields.Selection(string=u'周末加班规则', selection=weekend_selection, default='00')
    weekend_money = fields.Float(string=u'固定金额', digits=(10, 2))
    weekend_multiple = fields.Float(string=u'倍数', digits=(10, 1))

    holiday_selection = [
        ('00', '基本工资/应出勤天数/8*加班小时*倍数'),
        ('01', '加班小时*固定金额'),
    ]
    holiday_deduction = fields.Selection(string=u'节假日加班规则', selection=holiday_selection, default='00')
    holiday_money = fields.Float(string=u'固定金额', digits=(10, 2))
    holiday_multiple = fields.Float(string=u'倍数', digits=(10, 1))

    # -----考勤------
    late_attendance_selection = [
        ('00', '迟到次数*扣款金额'),
    ]
    late_attendance_deduction = fields.Selection(string=u'考勤迟到规则', selection=late_attendance_selection, default='00')
    late_attendance_money = fields.Float(string=u'扣款金额', digits=(10, 2))

    notsigned_selection = [
        ('00', '忘记打款次数*扣款金额'),
    ]
    notsigned_deduction = fields.Selection(string=u'忘记打卡规则', selection=notsigned_selection, default='00')
    notsigned_money = fields.Float(string=u'扣款金额', digits=(10, 2))

    early_selection = [
        ('00', '早退次数*扣款金额'),
    ]
    early_deduction = fields.Selection(string=u'早退打卡规则', selection=early_selection, default='00')
    early_money = fields.Float(string=u'扣款金额', digits=(10, 2))

    
    def compute_leave_deduction(self, base_wage, days, hours):
        """
        计算事假
        :param base_wage: 基本工资
        :param days:  出勤天数
        :param hours: 事假缺勤小时
        :return:
        """
        if self.leave_deduction == '00':
            # ('基本工资/应出勤天数/8*请假小时'
            return base_wage / days / 8 * hours
        elif self.leave_deduction == '01':
            # '基本工资/应出勤天数*请假小时'
            return base_wage / days * hours
        else:
            # (按次数) 次数*每次事假扣款
            return (hours / self.hour_leave_number) * self.leave_money

    
    def compute_sick_absence(self, base_wage, days, hours):
        """
        计算病假扣款
        :param base_wage:
        :param days:
        :param hours:
        :return:
        """
        if self.sick_deduction == '00':
            # 基本工资/2/应出勤天数/8*请假小时
            return base_wage/2/days/8*hours
        elif self.sick_deduction == '01':
            # 基本工资/应出勤天数*请假小时*病假扣款比例
            return base_wage / days * hours * self.sick_deduction_ratio
        elif self.sick_deduction == '02':
            # 基本工资/应出勤天数*请假小时/8*病假扣款比例
            return base_wage / days * hours / 8 * self.sick_deduction_ratio
        else:
            # (按次数) 次数*每次病假扣款')
            return int(hours/self.hour_sick_number) * self.sick_money

    
    def compute_work_overtime(self, base_wage, days, hours):
        """
        计算工作日加班费用
        :param base_wage:
        :param days:
        :param hours:
        :return:
        """
        if self.work_overtime_deduction == '00':
            # 基本工资/应出勤天数/8*加班小时*倍数
            return base_wage/days/8*hours*self.work_overtime_multiple
        else:
            # 加班小时*固定金额
            return hours * self.work_overtime_money

    
    def compute_weekend_overtime(self, base_wage, days, hours):
        """
        计算周末加班费用
        :param base_wage:
        :param days:
        :param hours:
        :return:
        """
        if self.weekend_deduction == '00':
            # 基本工资/应出勤天数/8*加班小时*倍数
            return base_wage/days/8*hours*self.weekend_multiple
        else:
            # 加班小时*固定金额
            return hours * self.weekend_multiple

    
    def compute_holiday_overtime(self, base_wage, days, hours):
        """
        计算节假日加班费用
        :param base_wage:
        :param days:
        :param hours:
        :return:
        """
        if self.holiday_deduction == '00':
            # 基本工资/应出勤天数/8*加班小时*倍数
            return base_wage/days/8*hours*self.holiday_multiple
        else:
            # 加班小时*固定金额
            return hours * self.holiday_money

    
    def compute_late_attendance(self, attendance_num):
        """
        计算迟到扣款费用
        :param attendance_num:
        :return:
        """
        if self.late_attendance_deduction == '00':
            # 迟到次数*扣款金额
            return attendance_num * self.late_attendance_money
        else:
            return 0

    
    def compute_notsigned_attendance(self, attendance_num):
        """
        计算忘记打卡扣款费用
        :param attendance_num:
        :return:
        """
        if self.notsigned_deduction == '00':
            # 忘记打款次数*扣款金额
            return attendance_num * self.notsigned_money
        else:
            return 0

    
    def compute_early_attendance(self, attendance_num):
        """
        计算早退扣款费用
        :param attendance_num:
        :return:
        """
        if self.early_deduction == '00':
            # 早退次数*扣款金额
            return attendance_num * self.early_money
        else:
            return 0

