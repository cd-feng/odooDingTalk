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


class EvaluationGroups(models.Model):
    _name = 'evaluation.groups.manage'
    _description = "考评组管理"
    _rec_name = 'name'
    _order = 'id'

    CycleType = [
        ('month', '月度'),
        ('quarter', '季度'),
        ('semiannual', '半年度'),
        ('year', '年度'),
        ('probation', '试用期'),
    ]

    active = fields.Boolean(string=u'Active', default=True)
    name = fields.Char(string='考评组名称', required=True, index=True)
    cycle_type = fields.Selection(string=u'周期类型', selection=CycleType, default='month')
    manage_user_ids = fields.Many2many(comodel_name='hr.employee',
                                       relation='evaluation_groups_evaluation_manage_user_rel', column1='groups_id',
                                       column2='emp_id', string=u'组管理员')
    evaluation_department_ids = fields.Many2many('hr.department', string=u'考评部门', help="按部门设置，新加入部门的员工将自动加入该考评组")
    no_evaluation_user_ids = fields.Many2many(comodel_name='hr.employee',
                                              relation='evaluation_groups_no_evaluation_users_rel', column1='groups_id',
                                              column2='emp_id', string=u'无需考评人员',
                                              help="从已选部门中排除不需要在本考评组或不需要考核的人员")
    evaluation_user_ids = fields.Many2many(comodel_name='hr.employee',
                                           relation='evaluation_groups_evaluation_users_rel',
                                           column1='groups_id', column2='emp_id', string=u'考评人员')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "考评组名称已存在!"),
    ]
