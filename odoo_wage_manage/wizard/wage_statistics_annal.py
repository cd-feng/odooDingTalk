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
from datetime import datetime, timedelta
import calendar
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


status_choice = [('0', '未使用'), ('1', '使用中'), ('2', '已失效'), ]
user_status_choice = [('0', '未审核'), ('1', '已审核'), ('2', '已失效'), ]

EditAttendanceType = [
    ('00', '基本工资/应出勤天数/8*请假小时'),
    ('01', '基本工资/应出勤天数*请假小时'),
    ('02', '(按次数) 次数*每次事假扣款'),
]

rate_choice = [('0', '年'), ('1', '月')]

check_status_choice = [('0', '正常'), ('1', '迟到'), ('2', '早退'), ('3', '旷工')]


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

    # emp_id = fields.Mnay2one('hr.employee.info', '员工')
    # attendance_date = fields.Date('考勤日期')
    # check_in = fields.Datetime('上班时间', null=True)
    # check_out = fields.Datetime('下班时间', null=True)
    # check_in_type = fields.Many2one('attendance.exception.status', string='上班打卡状态')
    # check_out_type = fields.Many2one('attendance.exception.status', string='下班打卡状态')
    # check_in_status = fields.Char('上午出勤情况', selection=check_status_choice)
    # check_out_status = fields.Char('下午出勤情况', selection=check_status_choice)
    check_status = fields.Boolean('是否异常')
    attendance_date_status = fields.Boolean('是否工作日',  default=True)

    @api.model_create_multi
    def create(self, vals_list):
        """
        支持批量新建考勤记录
        :return:
        """
        return super(AttendanceInfo, self).create(vals_list)




# class AttendanceTotal(models.Model):
#     _description = '考勤月报表'
#     _name = 'attendance.total'
#     _rec_name = 'name'

#     emp_id = fields.Mnay2one('hr.employee.info', string='员工')
#     section_date = fields.Char('汇总区间')
#     arrive_total = fields.Float('应到天数')
#     real_arrive_total = fields.Float('实到天数')
#     notsigned_attendance_num = fields.Float('旷工天数')
#     late_total = fields.Float('迟到/早退次数')
#     sick_leave_total = fields.Float('病假天数')
#     personal_leave_total = fields.Float('事假天数')
#     annual_leave_total = fields.Float('年假天数')
#     marriage_leave_total = fields.Float('婚假天数')
#     bereavement_leave_total = fields.Float('丧假天数')
#     paternity_leave_total = fields.Float('陪产假天数')
#     maternity_leave_total = fields.Float('产假天数')
#     work_related_injury_leave_total = fields.Float('工伤假天数')
#     home_leave_total = fields.Float('探亲假天数')
#     travelling_total = fields.Float('出差天数')
#     other_leave_total = fields.Float('其他假天数')


class WageEmpAttendanceAnnal(models.TransientModel):
    _description = '计算考勤结果'
    _name = 'wage.employee.attendance.annal.transient'

    SourceType = [
        ('dingding', '钉钉考勤结果'),
        ('odoo', 'Odoo出勤记录'),
        ('and', '两者同时获取')
    ]

    soure_type = fields.Selection(string=u'考勤结果来源', selection=SourceType, default='odoo', required=True)
    start_date = fields.Date(string=u'考勤开始日期', required=True)
    end_date = fields.Date(string=u'考勤结束日期', required=True)
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='attendance_total_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def compute_attendance_result(self):
        """
        立即计算考勤结果
        :return:
        """

        self.attendance_total_cal(self.emp_ids, self.start_date, self.end_date)
        
    def date_range(self, start_date, end_date):
        """
        生成一个 起始时间 到 结束时间 的一个列表
        TODO 起始时间和结束时间相差过大时，考虑使用 yield
        :param start_date:
        :param end_date:
        :return:
        """
        date_tmp = [start_date, ]
        # print(date_tmp[-1])
        while date_tmp[-1] < end_date:
            date_tmp.append(date_tmp[-1] + timedelta(days=1))
        return date_tmp

    # 获取原始打卡数据
    @api.multi
    def get_original_card_dict(self, emp_one, start_date, end_date):

        # attendance_card 是 日期加时间 ，只有一天的情况下，会出现问题
        original_card_dict_list = self.env['hr.attendance.result'].sudo().search([('emp_id', '=', emp_one.id), (
            'check_in', '<=', datetime(end_date.year, end_date.month, end_date.day) + timedelta(days=1)), ('check_in', '>=', start_date)])

        return original_card_dict_list

    # 生成考勤日报表
    @api.multi
    def attendance_cal(self, emp_list, start_date, end_date):

        # 获取排班信息 get_scheduling_info_dict
        # 获取班次信息 get_shift_info_dict
        # 获取签卡数据 get_edit_attendance_dict
        # 获取请假拆分后的数据 get_leave_detail_dict
        # TODO 获取出差数据
        # 获取原始打卡数据 get_original_card_dict
        # 数据整合 数据结构
        # 数据写入
        # 获取班次信息 get_shift_info_dict
        # shift_info_dict = get_shift_info_dict()
        # 考勤数据列表
        # attendance_info_list = []
        for emp in emp_list:
            # 删除已存在的
            old_attendance_info = self.env['attendance.info'].sudo().search(
                [('employee_id', '=', emp.id), ('workDate', '>=', start_date), ('workDate', '<=', end_date)])
            if old_attendance_info:
                old_attendance_info.sudo().unlink()
            # # 获取排班信息 get_scheduling_info_dict
            # scheduling_info_dict = get_scheduling_info_dict(emp, start_date, end_date)
            # # 获取签卡数据 get_edit_attendance_dict
            # edit_attendance_dict = get_edit_attendance_dict(emp, start_date, end_date)
            # # 获取请假拆分后的数据 get_leave_detail_dict
            # leave_detail_dict = get_leave_detail_dict(emp, start_date, end_date)
            # 获取原始打卡数据 get_original_card_dict
            # original_card_dict = self.get_original_card_dict(emp, start_date, end_date)
            # 整合打卡、签卡、请假数据，赋值
            # print(scheduling_info_dict, edit_attendance_dict, leave_detail_dict, original_card_dict)
            for date in self.date_range(start_date, end_date):
                work_date_attendance_result = self.env['hr.attendance.result'].sudo().search(
                    [('emp_id', '=', emp.id), ('work_date', '=', date)])

                OnDuty_list = list()
                OffDuty_list = list()
                for rec in work_date_attendance_result:
                    data = {
                        'employee_id': emp.id,
                        'workDate': rec.work_date,  # 工作日
                        'ding_group_id': rec.ding_group_id.id,
                    }
                    if rec.check_type == 'OnDuty':
                        data.update(
                            {'check_in': rec.check_in,
                             'on_planId': rec.plan_id,
                             'on_timeResult': rec.timeResult,
                             'on_sourceType': rec.sourceType
                             })
                        OnDuty_list.append(data)
                    else:
                        data.update({
                            'check_out': rec.check_in,
                            'off_planId': rec.plan_id,
                            'off_timeResult': rec.timeResult,
                            'off_sourceType': rec.sourceType
                        })
                        OffDuty_list.append(data)
                # 上班考勤结果列表与下班考勤结果列表按时间排序后合并
                OnDuty_list.sort(key=lambda x: x['check_in'])
                # logging.info(">>>获取OnDuty_list结果%s", OnDuty_list)
                OffDuty_list.sort(key=lambda x: x['check_out'])
                # logging.info(">>>获取OffDuty_list结果%s", OffDuty_list)
                duty_list = list()
                on_planId_list = list()
                for onduty in OnDuty_list:
                    for offduty in OffDuty_list:
                        datetime_check_out = offduty.get('check_out')
                        datetime_check_in = onduty.get('check_in')
                        if int(offduty.get('off_planId')) == int(onduty.get('on_planId')) + 1:
                            duty_tmp = dict(onduty, **offduty)
                            duty_list.append(duty_tmp)
                            on_planId_list.append(onduty.get('on_planId'))
                        elif datetime_check_out > datetime_check_in and \
                                onduty.get('on_planId') not in on_planId_list:
                            duty_tmp = dict(onduty, **offduty)
                            duty_list.append(duty_tmp)
                            on_planId_list.append(onduty.get('on_planId'))
                # 剩余还未匹配到下班记录的考勤（如当天）
                for onduty in OnDuty_list:
                    if onduty.get('on_planId') not in on_planId_list:
                        duty_list.append(onduty)
                # 将合并的考勤导入odoo考勤
                duty_list.sort(key=lambda x: x['check_in'])
                logging.info(">>>获取duty_list结果%s", duty_list)
                # 新建记录
                self.env['attendance.info'].sudo().create(duty_list)

                # if original_card_dict.get(date):
                #     # 判断原始打卡时间是否在打卡区间内
                #     if original_card_dict.get(date).get('min') <= shift_info_dict[shift_name].check_in_end:
                #         check_in = original_card_dict.get(date).get('min')
                #         check_in_type = attendance_exception_status_card_normal
                #     if original_card_dict.get(date).get('max') >= shift_info_dict[shift_name].check_out_start:
                #         check_out = original_card_dict.get(date).get('max')
                #         check_out_type = attendance_exception_status_card_normal
                # 检索签卡，如果有，覆盖
                # if edit_attendance_dict.get(date):
                #     if edit_attendance_dict.get(date).get('edit_attendance_time_start') is not None:
                #         check_in = edit_attendance_dict.get(date)['edit_attendance_time_start']
                #         check_in_type = edit_attendance_dict.get(date)['edit_attendance_time_start_type']
                #     if edit_attendance_dict.get(date).get('edit_attendance_time_end') is not None:
                #         check_out = edit_attendance_dict.get(date)['edit_attendance_time_end']
                #         check_out_type = edit_attendance_dict.get(date)['edit_attendance_time_end_type']
                # 检索请假， 如果有，覆盖
                # if leave_detail_dict.get(date):
                #     if leave_detail_dict.get(date).get('leave_detail_time_start') is not None:
                #         check_in = leave_detail_dict.get(date)['leave_detail_time_start']
                #         check_in_type = leave_detail_dict.get(date)['leave_detail_time_start_type']
                #     if leave_detail_dict.get(date).get('leave_detail_time_end') is not None:
                #         check_out = leave_detail_dict.get(date)['leave_detail_time_end']
                #         check_out_type = leave_detail_dict.get(date)['leave_detail_time_end_type']
                # attendance_info_tmp = ExceptionAttendanceInfo(emp=emp, attendance_date=date, check_in=check_in,
                #                                               check_out=check_out, check_in_type=check_in_type,
                #                                               check_out_type=check_out_type,
                #                                               shift_info=shift_info_dict[shift_name]).attendance_info_ins()
        #         attendance_info_tmp = {
        #             'emp_id': emp.id,
        #             'attendance_date': date,
        #             'check_in': check_in,
        #             'check_out': check_out,
        #             'check_in_type': check_in_type,
        #             'check_out_type': check_out_type,
        #             'shift_info': shift_info_dict[shift_name]).attendance_info_ins(),
        #             'check_in_status': ccc,
        #         }
        #         attendance_info_list.append(attendance_info_tmp)
        # self.env['attendance.info'].create(attendance_info_list)

    def attendance_total_cal(self, emp_list, start_date, end_date):
        """
        考勤汇总计算
        :return:
        """
        self.ensure_one()
        # 生成考勤日报表
        self.attendance_cal(emp_list, start_date, end_date)
        attendance_total_ins_list = []
        for emp in emp_list:
            # 获取年月，取得区间月份
            month = 0
            if end_date.year - start_date.year == 0:
                month = end_date.month - start_date.month
            elif end_date.year - start_date.year >= 1:
                month = end_date.month - start_date.month + (end_date.year - start_date.year) * 12
            start_date_tmp = start_date.replace(day=1)
            for num in range(month + 1):
                current_month_num = calendar.monthrange(start_date_tmp.year, start_date_tmp.month)[1]
                # 删除原有记录
                del_question_start = self.env['wage.employee.attendance.annal'].sudo().search(
                    [('employee_id', '=', emp.id), ('attend_code', '=', start_date_tmp.strftime('%Y/%m'))])
            if del_question_start:
                del_question_start.sudo().unlink()
            attendance_info_dict_list = self.env['attendance.info'].sudo().search([('employee_id', '=', emp.id), (
                'workDate', '>=', start_date_tmp), ('workDate', '<=', start_date_tmp.replace(day=current_month_num))])
            # check_status_choice = (('0', '正常'), ('1', '迟到'), ('2', '早退'), ('3', '旷工'))
            logging.info(">>>获取的考勤结果:%s", attendance_info_dict_list)
            attendance_total_ins = self.attendance_total_cal_sum(emp, start_date_tmp, attendance_info_dict_list)
            attendance_total_ins_list.append(attendance_total_ins)
            start_date_tmp += timedelta(days=current_month_num)
        self.env['wage.employee.attendance.annal'].sudo().create(attendance_total_ins_list)

    # 统计月应出勤及请假天数
    @api.multi
    def attendance_total_cal_sum(self, emp, start_date, attendance_info_dict_list):
        arrive_total = real_arrive_total = notsigned_attendance_num = late_total = 0
        leave_dict = {'病假': 0, '事假': 0, '年假': 0, '婚假': 0, '丧假': 0, '陪产假': 0, '产假': 0, '工伤假': 0, '探亲假': 0, '出差（请假）': 0,
                      '其他假': 0}
        for one in attendance_info_dict_list:
            # 统计考勤
            if one.attendance_date_status:
                arrive_total = arrive_total + 1
                if one.on_timeResult == 'NotSigned':
                    notsigned_attendance_num = notsigned_attendance_num + 1
                elif one.on_timeResult == 'Late':
                    late_total = late_total + 1
                if one.off_timeResult == 'NotSigned':
                    notsigned_attendance_num = notsigned_attendance_num + 1
                elif one.off_timeResult == 'Early':
                    late_total = late_total + 1
            # 统计假期
            # if leave_dict.get(one.check_in_type_id) is not None:
            #     leave_dict[one.check_in_type_id] += 1
            # 实到天数 real_arrive_total 非请假的所有出勤天数
            elif one.attendance_date_status:
                if one.on_timeResult != 'NotSigned':
                    real_arrive_total = real_arrive_total + 1
            # if leave_dict.get(one.check_out_type_id) is not None:
            #     leave_dict[one.check_out_type_id] = leave_dict[one.check_out_type_id] + 1
            # 实到天数 real_arrive_total 非请假的所有出勤天数
            elif one.attendance_date_status:
                if one.off_timeResult != 'NotSigned':
                    real_arrive_total = real_arrive_total + 1

        attendance_total_ins = {'employee_id': emp.id,
                                'section_date': start_date.strftime('%Y/%m'),
                                'arrive_total': arrive_total,
                                'real_arrive_total': real_arrive_total,
                                'notsigned_attendance_num': notsigned_attendance_num,
                                'late_total': late_total,
                                'sick_leave_total': leave_dict['病假'],
                                'personal_leave_total': leave_dict['事假'],
                                'annual_leave_total': leave_dict['年假'],
                                'marriage_leave_total': leave_dict['婚假'],
                                'bereavement_leave_total': leave_dict['丧假'],
                                'paternity_leave_total': leave_dict['陪产假'],
                                'maternity_leave_total': leave_dict['产假'],
                                'work_related_injury_leave_total': leave_dict['工伤假'],
                                'home_leave_total': leave_dict['探亲假'],
                                'travelling_total': leave_dict['出差（请假）'],
                                'other_leave_total': leave_dict['其他假'],
                                }
        return attendance_total_ins


class WageEmpPerformanceManage(models.TransientModel):
    _description = '从绩效计算结果'
    _name = 'wage.employee.performance.manage.transient'

    start_date = fields.Date(string=u'开始日期', required=True)
    end_date = fields.Date(string=u'结束日期', required=True)

    @api.multi
    def compute_performance_result(self):
        """
        从绩效计算结果
        :return:
        """
        self.ensure_one()
        # raise UserError("暂未实现！！！")
        return {'type': 'ir.actions.act_window_close'}
