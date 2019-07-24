# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_user_health_info = fields.Boolean(string="员工今日步数")
    auto_dept_health_info = fields.Boolean(string="部门今日步数")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            auto_user_health_info=self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_user_health_info'),
            auto_dept_health_info=self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_dept_health_info'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('dingding_health.auto_user_health_info', self.auto_user_health_info)
        self.env['ir.config_parameter'].sudo().set_param('dingding_health.auto_dept_health_info', self.auto_dept_health_info)
