# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    ding_id = fields.Char(string='钉钉标签ID', index=True)
    ding_category_type = fields.Char(string='标签分类名')
    company_id = fields.Many2one('res.company', string='关联公司', default=lambda self: self.env.company)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    ding_id = fields.Char(string='钉钉ID')
    ding_company_name = fields.Char(string='钉钉联系人公司')
    ding_employee_id = fields.Many2one('hr.employee', string=u'钉钉负责人', ondelete='set null', domain=[('ding_id', '!=', '')])

