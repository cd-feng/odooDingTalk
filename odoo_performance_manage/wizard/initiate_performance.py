# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class InitiatePerformanceAssessment(models.TransientModel):
    _name = 'initiate.performance.assessment'
    _description = "发起绩效考核"
    _order = 'id'

    AssessmentType = [
        ('month', '月度'),
        ('quarter', '季度'),
        ('semiannual', '半年度'),
        ('year', '年度'),
        ('probation', '试用期'),
    ]

    assessment_type = fields.Selection(string=u'考核类型', selection=AssessmentType, default='month')
    start_date = fields.Date(string=u'开始日期', required=True)
    end_date = fields.Date(string=u'截至日期', required=True)
    evaluation_ids = fields.Many2many(comodel_name='evaluation.groups.manage', string=u'考评组')
    is_email = fields.Boolean(string=u'Email通知')

    @api.onchange('assessment_type')
    def _onchange_assessment_type(self):
        """
        :return:
        """
        for res in self:
            if res.assessment_type in ['quarter', 'semiannual', 'probation']:
                raise UserError("当前版本仅支持类型为月度或年度，如需其他类型请购买完整版！")
            if res.assessment_type:
                res.evaluation_ids = [(2, 0, res.evaluation_ids.ids)]
                return {'domain': {'evaluation_ids': [('cycle_type', '=', self.assessment_type)]}}

    @api.multi
    def initiate_performance(self):
        """
        发起考核
        :return:
        """
        self.ensure_one()
        if self.assessment_type in ['quarter', 'semiannual', 'probation']:
            raise UserError("当前版本仅支持类型为月度或年度，如需其他类型请购买完整版！")
        asset_data = {
            'assessment_type': self.assessment_type,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
        }
        for evaluation in self.evaluation_ids:
            asset_data['evaluation_id'] = evaluation.id
            # 读取维度和指标模板信息
            line_list = list()
            for template in evaluation.template_ids:
                # 读取指标
                indicator_list = list()
                for indicator in template.indicator_ids:
                    indicator_data = {
                        'indicator_id': indicator.id,
                        'threshold_value': indicator.threshold_value,
                        'target_value': indicator.target_value,
                        'challenge_value': indicator.challenge_value,
                        'assessment_criteria': indicator.assessment_criteria,
                        'weights': indicator.weights,
                        'notes': indicator.notes,
                    }
                    if indicator.indicator_type == 'bonus':
                        indicator_data.update({'extra_end': indicator.extra_end})
                    elif indicator.indicator_type == 'deduction':
                        indicator_data.update({'extra_end': indicator.deduction_end})
                    else:
                        indicator_data.update({'extra_end': 0})
                    indicator_list.append((0, 0, indicator_data))
                # 维度信息
                line_data = {
                    'dimension_id': template.dimension_id.id,
                    'dimension_weights': template.dimension_weights,
                    'library_ids': indicator_list,
                }
                line_list.append((0, 0, line_data))
            asset_data['line_ids'] = line_list
            # 读取考评人员
            for employee in evaluation.evaluation_user_ids:
                asset_data['employee_id'] = employee.id
                asset_data['message_follower_ids'] = False
                self.env['performance.assessment'].create(asset_data)
        if self.is_email:
            print("发送员工邮件")
        return {'type': 'ir.actions.act_window_close'}


