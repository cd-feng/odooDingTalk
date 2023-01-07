# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DingTalkApprovalLog(models.Model):
    _name = 'dingtalk.approval.log'
    _description = '钉钉审批日志'
    _rec_name = 'res_model'

    res_model = fields.Char(string="模型名称")
    res_id = fields.Integer(string="记录ID")
    process_instance = fields.Char(string="钉钉实例ID")
    user_id = fields.Many2one(comodel_name="res.users", string="创建人")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="员工")
    approval_content = fields.Char(string="消息内容")
    approval_time = fields.Datetime(string="记录时间", default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', '公司')


