# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pm_calculation_rules = fields.Selection(string=u'计算规则', selection=[('and', '量化指标和行为价值观指标合并计算')])
    pm_grade_rules = fields.Selection(string=u'绩效等级规则', selection=[('distributed', '强制正态分布'), ('interval', '分数区间对应')])
    pm_dingding_hrm = fields.Boolean(string=u'对接钉钉智能人事')
    pm_email_remind = fields.Boolean(string=u'待办邮件提醒')
    pm_score_name = fields.Char(string='满分分制名称')
    pm_score_value = fields.Char(string='满分值')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            pm_calculation_rules=self.env['ir.config_parameter'].sudo().get_param('odoo_performance_manage.pm_calculation_rules') or 'and',
            pm_grade_rules=self.env['ir.config_parameter'].sudo().get_param('odoo_performance_manage.pm_grade_rules') or 'interval',
            pm_dingding_hrm=self.env['ir.config_parameter'].sudo().get_param('odoo_performance_manage.pm_dingding_hrm'),
            pm_email_remind=self.env['ir.config_parameter'].sudo().get_param('odoo_performance_manage.pm_email_remind'),
            pm_score_name=self.env['ir.config_parameter'].sudo().get_param('odoo_performance_manage.pm_score_name') or u'优秀',
            pm_score_value=self.env['ir.config_parameter'].sudo().get_param('odoo_performance_manage.pm_score_value') or '100',
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('odoo_performance_manage.pm_calculation_rules', self.pm_calculation_rules)
        self.env['ir.config_parameter'].sudo().set_param('odoo_performance_manage.pm_grade_rules', self.pm_grade_rules)
        self.env['ir.config_parameter'].sudo().set_param('odoo_performance_manage.pm_dingding_hrm', self.pm_dingding_hrm)
        self.env['ir.config_parameter'].sudo().set_param('odoo_performance_manage.pm_email_remind', self.pm_email_remind)
        self.env['ir.config_parameter'].sudo().set_param('odoo_performance_manage.pm_score_name', self.pm_score_name)
        self.env['ir.config_parameter'].sudo().set_param('odoo_performance_manage.pm_score_value', self.pm_score_value)

