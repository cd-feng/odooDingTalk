# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import json
import logging
import time
import requests
from requests import ReadTimeout
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrAttendanceResult(models.Model):
    _name = "hr.attendance.result"
    _rec_name = 'emp_id'
    _description = "员工打卡结果"

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
        ('USER', '用户打卡'),
        ('BOSS', '老板改签'),
        ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'),
        ('AUTO_CHECK', '自动打卡')
    ]
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    ding_group_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'钉钉考勤组')
    plan_id = fields.Many2one(comodel_name='hr.dingding.plan', string=u'排班')
    ding_plan_id = fields.Char(string='钉钉排班ID')
    record_id = fields.Char(string='唯一标识ID', help="钉钉设置的值为id，odoo中为record_id")
    work_date = fields.Date(string=u'工作日')
    work_month = fields.Char(string='年月字符串', help="为方便其他模块按照月份获取数据时使用", index=True)
    check_type = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')], index=True)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    approveId = fields.Char(string='关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    procInstId = fields.Char(string='审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    procInst_title = fields.Char(string='审批标题')
    baseCheckTime = fields.Datetime(string=u'基准时间', help="计算迟到和早退，基准时间")
    check_in = fields.Datetime(string="实际打卡时间", required=True, help="实际打卡时间,  用户打卡时间的毫秒数")
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult, index=True)
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)

    @api.model
    def create(self, values):
        """
        创建时触发
        :param values:
        :return:
        """
        if values['work_date']:
            values.update({'work_month': "{}/{}".format(values['work_date'][:4], values['work_date'][5:7])})
        return super(HrAttendanceResult, self).create(values)
