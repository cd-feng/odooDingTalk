# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

from odoo import api, fields, models


class DingDingApprovalRecord(models.Model):
    _name = 'dingtalk.approval.record'
    _description = '审批记录'
    _rec_name = 'process_instance'

    APPROVALRESULT = [('load', '等待'), ('agree', '同意'), ('refuse', '拒绝'), ('redirect', '转交')]

    model_id = fields.Many2one(comodel_name='ir.model', string='模型', index=True)
    rec_id = fields.Integer(string="记录ID", index=True)
    process_instance = fields.Char(string="审批实例ID", index=True, required=True)
    emp_id = fields.Many2one(comodel_name="hr.employee", string="操作人", required=True)
    approval_type = fields.Selection(string="类型", selection=[('start', '开始'), ('comment', '评论'), ('finish', '结束')])
    approval_result = fields.Selection(string=u'审批结果', selection=APPROVALRESULT)
    approval_content = fields.Char(string="内容")
    approval_time = fields.Datetime(string="记录时间", default=fields.Datetime.now)
