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


class DimensionManage(models.Model):
    _name = 'performance.dimension.manage'
    _description = "维度管理"
    _rec_name = 'name'
    _order = 'id'

    DimensionType = [
        ('quantitative', '量化指标'),
        ('behavior', '行为价值观指标'),
        ('bonus', '加分项'),
        ('deduction', '扣分项'),
    ]

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char(string='维度名称', required=True, index=True)
    dimension_type = fields.Selection(string=u'维度类型', selection=DimensionType, default='quantitative', index=True)
    dimension_weights = fields.Integer(string=u'维度权重')
    index_number = fields.Selection(string=u'指标数量', selection=[('unlimited', '不限'), ('limit', '自定义')], default='unlimited')
    user_index_number = fields.Integer(string=u'指标自定义数量')
    index_weights = fields.Selection(string=u'指标权重', selection=[('unlimited', '不限'), ('limit', '自定义')], default='unlimited')
    user_index_weights = fields.Integer(string=u'指标自定义权重')
    is_add_index = fields.Boolean(string=u'可在制定目标时增加指标?', help="设定在目标制定、目标确认环节，这个维度下能不能再增加指标", default=True)
    index_res_type = fields.Selection(string=u'指标评分方式', selection=[('00', '指标评分加和计算'), ('01', '指标评分加权计算'), ], default='00')

