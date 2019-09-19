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


class IndicatorLabel(models.Model):
    _name = 'performance.indicator.label'
    _description = "指标标签"

    name = fields.Char(string='标签名称', index=True)


class IndicatorLibrary(models.Model):
    _name = 'performance.indicator.library'
    _description = "指标库"
    _rec_name = 'name'
    _order = 'id'

    IndicatorType = [
        ('quantitative', '量化指标'),
        ('behavior', '行为价值观指标'),
        ('bonus', '加分项'),
        ('deduction', '扣分项'),
    ]

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char(string='指标名称', required=True, index=True)
    indicator_type = fields.Selection(string=u'指标类型', selection=IndicatorType, default='quantitative', required=True)

    indicator_unit = fields.Char(string='量化指标单位')
    threshold_value = fields.Integer(string='门槛值')
    target_value = fields.Char(string='目标值')
    challenge_value = fields.Integer(string='挑战值')
    assessment_criteria = fields.Text(string='考核标准')
    weights = fields.Integer(string=u'权重')
    notes = fields.Text(string=u'备注')
    grading_method = fields.Selection(string=u'评分方式', selection=[('00', '直接输入分数'), ('01', '评分公式计算')], default='00')
    is_required = fields.Boolean(string=u'必选', help="选中时，此指标将作为不可修改的默认指标项，员工必须参与考评")
    designated_scorer = fields.Boolean(string=u'指定评分人', help="开启后，该指标如被制定目标引用，该指标将由指定的人进行评分")
    scorer_user = fields.Many2one(comodel_name='hr.employee', string=u'评分人')
    label_ids = fields.Many2many('performance.indicator.label',  string='标签')

    extra_standard = fields.Text(string=u'加分标准')
    extra_end = fields.Integer(string=u'加分上限')
    deduction_standard = fields.Text(string=u'扣分标准')
    deduction_end = fields.Integer(string=u'扣分上限')
