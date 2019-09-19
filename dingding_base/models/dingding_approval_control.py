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


class DingDingApprovalControl(models.Model):
    _name = 'dingding.approval.control'
    _description = "审批单据关联"
    _rec_name = 'oa_model_id'

    oa_model_id = fields.Many2one(comodel_name='ir.model', string=u'Odoo模型', required=True, index=True)
    template_id = fields.Many2one(comodel_name='dingding.approval.template', string=u'钉钉审批模板', required=True, index=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)

    _sql_constraints = [
        ('oa_model_id_uniq', 'unique(oa_model_id)', u'已存在Odoo模型对应的审批模板!'),
    ]

    @api.model
    def get_oa_model(self):
        oa_models = self.env['dingding.approval.control'].sudo().search([])
        model_list = list()
        for oa_model in oa_models:
            model_list.append(oa_model.oa_model_id.model)
        return model_list
