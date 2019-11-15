# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class DingTalkHrmDimissionList(models.Model):
    _name = 'dingtalk.hrm.dimission.list'
    _description = "离职员工信息"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'emp_id'

    REASONTYPE = [
        ('1', '家庭原因'),
        ('2', '个人原因'),
        ('3', '发展原因'),
        ('4', '合同到期不续签'),
        ('5', '协议解除'),
        ('6', '无法胜任工作'),
        ('7', '经济性裁员'),
        ('8', '严重违法违纪'),
        ('9', '其他'),
    ]
    PRESTATUS = [
        ('1', '待入职'),
        ('2', '试用期'),
        ('3', '正式'),
    ]
    active = fields.Boolean(string=u'Active', default=True)
    ding_id = fields.Char(string='员工用户id')
    emp_id = fields.Many2one(comodel_name='dingtalk.employee.roster', string='员工', required=True)
    last_work_day = fields.Datetime(string='最后工作时间')
    reason_memo = fields.Text(string="离职原因")
    reason_type = fields.Selection(string='离职类型', selection=REASONTYPE)
    pre_status = fields.Selection(string='离职前工作状态', selection=PRESTATUS)
    handover_userid = fields.Many2one(comodel_name='hr.employee', string='离职交接人')
    mainDeptId = fields.Many2one(comodel_name='hr.department', string=u'离职前部门')
    state = fields.Selection(string=u'离职状态', selection=[('1', '待离职'), ('2', '已离职')])
