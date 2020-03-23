# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020 SuXueFeng GNU
###################################################################################

from odoo import models, fields, api, exceptions, _


class HrAttendance(models.AbstractModel):
    _inherit = "hr.attendance"

    TimeResult = [
        ('Normal', '正常'),
        ('Early', '早退'),
        ('Late', '迟到'),
        ('SeriousLate', '严重迟到'),
        ('Absenteeism', '旷工迟到'),
        ('NotSigned', '未打卡'),
    ]
    SourceType = [
        ('ATM', '考勤机'),
        ('BEACON', 'IBeacon'),
        ('DING_ATM', '钉钉考勤机'),
        ('USER', '用户打卡'),
        ('BOSS', '老板改签'),
        ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'),
        ('AUTO_CHECK', '自动打卡')
    ]

    ding_group_id = fields.Many2one(comodel_name='dingtalk.simple.groups', string=u'钉钉考勤组')
    ding_plan_id = fields.Char(string='钉钉排班ID')
    work_date = fields.Date(string=u'工作日')
    work_month = fields.Char(string='年月字符串', help="为方便其他模块按照月份获取数据时使用", index=True)
    source_type = fields.Selection(string=u'数据来源', selection=SourceType)
    time_result = fields.Selection(string="打卡结果", selection=TimeResult)

    @api.model
    def create(self, vals):
        """
        创建时触发
        :param vals:
        :return:
        """
        if vals.get('work_date'):
            vals.update({'work_month': "{}/{}".format(vals['work_date'][:4], vals['work_date'][5:7])})
        return super(HrAttendance, self).create(vals)

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        return

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    return
                    # raise exceptions.ValidationError(_('%s的"签出"时间不能早于“签入”时间' % attendance.employee_id.name))
