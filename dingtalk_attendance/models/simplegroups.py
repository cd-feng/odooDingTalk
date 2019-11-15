# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingTalkSimpleGroups(models.Model):
    _name = 'dingtalk.simple.groups'
    _rec_name = 'name'
    _description = '考勤组'

    ATTENDANCETYPE = [
        ('FIXED', '固定排班'),
        ('TURN', '轮班排班'),
        ('NONE', '无班次')
    ]

    name = fields.Char(string='名称', index=True)
    group_id = fields.Char(string='钉钉考勤组ID', index=True)
    s_type = fields.Selection(string=u'考勤类型', selection=ATTENDANCETYPE, default='NONE')
    member_count = fields.Integer(string=u'成员人数')
    manager_list = fields.Many2many(comodel_name='hr.employee', relation='simple_groups_manage_emp_rel',
                                    column1='group_id', column2='emp_id', string=u'负责人')
    dept_name_list = fields.Many2many('hr.department', string=u'关联部门')
    classes_list = fields.Char(string='班次时间展示')
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='simple_groups_and_users_rel',
                               column1='group_id', column2='emp_id', string=u'成员列表')
    list_ids = fields.One2many(comodel_name='dingtalk.simple.groups.list', inverse_name='simple_id', string=u'班次列表')


class DingTalkSimpleGroupsList(models.Model):
    _description = "班次列表"
    _name = 'dingtalk.simple.groups.list'
    _rec_name = 'class_name'

    simple_id = fields.Many2one(comodel_name='dingtalk.simple.groups', string=u'考勤组', index=True)
    class_name = fields.Char(string='考勤班次名称', index=True)
    class_id = fields.Char(string='考勤班次Id', index=True)
    # setting
    class_setting_id = fields.Char(string='考勤组班次id')
    rest_begin_time = fields.Char(string='休息开始时间', help="只有一个时间段的班次有")
    check_time = fields.Char(string='开始时间', help="开始时间")
    permit_late_minutes = fields.Char(string='允许迟到时长(分钟)', help="允许迟到时长，单位分钟")
    work_time_minutes = fields.Char(string='工作时长', help="单位分钟，-1表示关闭该功能")
    rest_end_time = fields.Char(string='休息结束时间', help="只有一个时间段的班次有")
    end_time = fields.Char(string='结束时间', help="结束时间")
    absenteeism_late_minutes = fields.Char(string='旷工迟到分钟', help="旷工迟到时长，单位分钟")
    serious_late_minutes = fields.Char(string='严重迟到分钟', help="严重迟到时长，单位分钟")
    is_off_duty_free_check = fields.Selection(string=u'强制打卡', selection=[('Y', '下班不强制打卡'), ('N', '下班强制打卡')])
    # sections
    time_ids = fields.One2many(comodel_name='dingtalk.simple.groups.list.time', inverse_name='list_id', string=u'打卡时间段')


class DingTalkSimpleGroupsListTime(models.Model):
    _description = "班次打卡时间段"
    _name = 'dingtalk.simple.groups.list.time'
    _rec_name = 'list_id'

    list_id = fields.Many2one(comodel_name='dingtalk.simple.groups.list', string=u'班次', index=True)
    across = fields.Char(string=u'打卡时间跨度')
    check_time = fields.Datetime(string=u'打卡时间')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])
