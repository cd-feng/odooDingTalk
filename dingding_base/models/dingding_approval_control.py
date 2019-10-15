# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng
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
###################################################################################
import logging
from odoo import api, fields, models
import inspect
import sys

_logger = logging.getLogger(__name__)


class DingDingApprovalControl(models.Model):
    _name = 'dingding.approval.control'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "审批配置"
    _rec_name = 'name'

    def _compute_domain(self):
        all_cls = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        odoo_cls = [getattr(cls[1], '_name') for cls in all_cls if cls[1].__bases__[0].__name__ == 'Model']  # 排除当前的对象
        odoo_cls += [model.model for model in self.env['ir.model'].search([('transient', '=', True)])]  # 排除临时对象
        return [('model', 'not in', odoo_cls)]

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char('名称', required=1, track_visibility='onchange')
    oa_model_id = fields.Many2one('ir.model', string=u'Odoo模型', index=True, domain=_compute_domain, track_visibility='onchange', ondelete="set null")
    template_id = fields.Many2one('dingding.approval.template', string=u'钉钉审批模板', index=True, track_visibility='onchange', ondelete="set null")
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)

    _sql_constraints = [
        ('oa_model_id_uniq', 'unique(oa_model_id)', u'已存在Odoo模型对应的审批模板!'),
    ]

    def action_reload_current_page(self):
        """
        配置审批后需要自动升级配置的模型对应的模块，然后刷新界面，专业版功能
        :return:
        """
        module_name = self.oa_model_id.modules
        module_names = module_name.replace(' ', '').split(',')
        current_module = self.env['ir.module.module'].search([('name', 'in', module_names)])
        current_module.button_immediate_upgrade()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
