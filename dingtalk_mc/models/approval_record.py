# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID


class DingDingApprovalRecord(models.Model):
    _name = 'dingtalk.approval.record'
    _description = '审批日志'
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
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company)

    @api.model
    def process_dingtalk_chat(self, model_id, rec_id, pi, emp_id, at, ar, ac, company_id):
        """
        接受来自钉钉回调的处理
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                self.env['dingtalk.approval.record'].with_user(SUPERUSER_ID).create({
                    'model_id': model_id,  # 模型
                    'rec_id': rec_id,  # 记录ID
                    'process_instance': pi,  # 审批实例ID
                    'emp_id': emp_id,  # 操作人
                    'approval_type': at,  # 类型
                    'approval_result': ar,  # 审批结果
                    'approval_content': ac,  # 内容
                    'company_id': company_id,  # 公司
                })
        return
