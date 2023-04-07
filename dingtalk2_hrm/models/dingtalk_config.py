# -*- coding: utf-8 -*-
from odoo import models, fields


class DingTalk2Config(models.Model):
    _inherit = 'dingtalk2.config'

    is_get_dimission_hrm = fields.Boolean(string="同步离职员工信息", default=False)
    auto_get_emp_roster = fields.Boolean(string="自动同步花名册", default=False)
    auto_sync_employees_system = fields.Boolean(string="更新花名册到员工", default=False)

