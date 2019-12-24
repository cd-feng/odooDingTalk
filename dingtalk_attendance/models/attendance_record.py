# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
from odoo import models, fields, api


class HrAttendanceRecord(models.Model):
    _name = "hr.attendance.record"
    _rec_name = 'userId'
    _description = "员工打卡详情"

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

    userId = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    record_id = fields.Char(string='唯一标识')
    groupId = fields.Many2one(comodel_name='dingding.simple.groups', string=u'考勤组', index=True)
    planId = fields.Many2one(comodel_name='hr.dingding.plan', string=u'班次', index=True)
    ding_plan_id = fields.Char(string='钉钉排班ID')
    workDate = fields.Date(string=u'工作日', index=True)
    corpId = fields.Char(string='企业ID')
    checkType = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')])
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult, index=True)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    approveId = fields.Char(string='关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    procInstId = fields.Char(string='审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    baseCheckTime = fields.Datetime(string=u'基准时间', help="计算迟到和早退，基准时间")
    userCheckTime = fields.Datetime(string="实际打卡时间", help="实际打卡时间,  用户打卡时间的毫秒数")
    userAddress = fields.Char(string='用户打卡地址')
    userLongitude = fields.Char(string='用户打卡经度')
    userLatitude = fields.Char(string='用户打卡纬度')
    outsideRemark = fields.Text(string='打卡备注')
