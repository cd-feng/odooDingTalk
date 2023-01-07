# -*- coding: utf-8 -*-
from odoo import fields, models


class DingDingApprovalButton(models.Model):
    _name = 'dingtalk.approval.model.button'
    _description = '钉钉审批模型按钮'
    _rec_name = 'name'

    model_id = fields.Many2one('ir.model', string='模型', index=True)
    model_model = fields.Char(string='模型名', related='model_id.model', store=True, index=True)
    name = fields.Char(string="按钮名称", index=True)
    function = fields.Char(string='按钮方法', index=True)
    modifiers = fields.Char(string="按钮属性值")
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.company)

    def name_get(self):
        return [(rec.id, "%s:%s" % (rec.model_id.name, rec.name)) for rec in self]
