# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ding_id = fields.Char(string='钉钉ID', index=True)
    ding_company_name = fields.Char(string='钉钉联系人公司')
    ding_employee_id = fields.Many2one('hr.employee', '钉钉负责人', ondelete='set null')

