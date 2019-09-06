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


class PerformanceGrade(models.Model):
    _name = 'performance.grade.manage'
    _description = "绩效等级"
    _rec_name = 'name'
    _order = 'interval_from'

    active = fields.Boolean(string=u'Active', default=True)
    grade_type = fields.Selection(string=u'等级类型', selection=[('distributed', '强制正态分布(未开发)'), ('interval', '分数区间对应')], default='interval', required=True, index=True)
    name = fields.Char(string='等级名称', required=True, index=True)
    interval_from = fields.Char(string='分数区间范围起', required=True, index=True)
    interval_end = fields.Char(string='分数区间范围止', required=True, index=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "等级名称已存在!"),
    ]


