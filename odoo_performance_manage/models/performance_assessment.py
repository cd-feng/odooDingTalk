# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
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


class PerformanceAssessment(models.Model):
    _name = 'performance.assessment'
    _description = "绩效考评"
    _rec_name = 'employee_id'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    PerState = [
        ('setting', '目标制定'),
        ('executing', '执行中'),
        ('result', '录入结果'),
        ('evaluation', '自评'),
        ('close', '结束'),
    ]
    AssessmentType = [
        ('month', '月度'),
        ('quarter', '季度'),
        ('semiannual', '半年度'),
        ('year', '年度'),
        ('probation', '试用期'),
    ]
    active = fields.Boolean(string=u'active', default=True)
    name = fields.Char(string='名称', track_visibility='onchange')
    evaluation_id = fields.Many2one(comodel_name='evaluation.groups.manage', string=u'考评组')
    performance_name = fields.Char(string='考评分组名称', help="根据类型拼接名称，用于分组")
    state = fields.Selection(string=u'考评状态', selection=PerState, default='setting', track_visibility='onchange')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'考评员工', index=True, required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'所属部门', index=True)
    assessment_type = fields.Selection(string=u'考核类型', selection=AssessmentType, default='month', required=True)
    start_date = fields.Date(string=u'开始日期', required=True, track_visibility='onchange')
    end_date = fields.Date(string=u'截至日期', required=True, track_visibility='onchange')
    line_ids = fields.One2many('performance.assessment.line', 'performance_id', string=u'绩效考评项目')
    notes = fields.Text(string=u'备注', track_visibility='onchange')

    @api.multi
    def summit_performance(self):
        """
        提交目标
        :return:
        """
        for res in self:
            res.state = 'executing'

    @api.constrains('assessment_type')
    def _constrains_assessment_type(self):
        """
        根据考评类型生成分组名称
        :return:
        """
        for res in self:
            if res.assessment_type == 'month':
                res.performance_name = "%s月绩效考核" % str(res.start_date)[:7]
            elif res.assessment_type == 'year':
                res.performance_name = "%s年度绩效考核" % str(res.start_date)[:4]

    @api.constrains('employee_id', 'performance_name')
    def _constrains_name(self):
        """
        生成name字段
        :return:
        """
        for res in self:
            res.name = "%s的%s" % (res.employee_id.name, res.performance_name)
            res.department_id = res.employee_id.department_id.id if res.employee_id.department_id else False


class PerformanceAssessmentLine(models.Model):
    _name = 'performance.assessment.line'
    _description = "绩效考评项目"
    _rec_name = 'dimension_id'

    performance_id = fields.Many2one(comodel_name='performance.assessment', string=u'绩效考评')
    sequence = fields.Integer(string=u'序号')
    dimension_id = fields.Many2one(comodel_name='performance.dimension.manage', string=u'考评维度', required=True)
    dimension_weights = fields.Integer(string=u'权重')
    library_ids = fields.One2many('performance.assessment.line.library', 'assessment_line_id', string=u'考评指标')

    @api.onchange('dimension_id')
    def _onchange_dimension_id(self):
        """
        :return:
        """
        if self.dimension_id:
            self.library_ids = False
            self.dimension_weights = self.dimension_id.dimension_weights


class PerformanceAssessmentLineLibrary(models.Model):
    _name = 'performance.assessment.line.library'
    _description = "考评指标"
    _rec_name = 'indicator_id'

    assessment_line_id = fields.Many2one(comodel_name='performance.assessment.line', string=u'绩效考评项目')
    dimension_id = fields.Many2one(comodel_name='performance.dimension.manage', string=u'考评维度')
    sequence = fields.Integer(string=u'序号')
    indicator_id = fields.Many2one(comodel_name='performance.indicator.library', string=u'考评指标', domain=[('name', '=', 'False')])
    extra_end = fields.Integer(string=u'加扣分上限')
    threshold_value = fields.Integer(string='门槛值')
    target_value = fields.Char(string='目标值')
    challenge_value = fields.Integer(string='挑战值')
    assessment_criteria = fields.Text(string='考核标准')
    weights = fields.Integer(string=u'权重')
    notes = fields.Text(string=u'备注')

    @api.onchange('dimension_id')
    def _onchange_dimension_id(self):
        """
        根据维度值动态返回过滤规则
        :return:
        """
        if self.dimension_id:
            self.indicator_ids = False
            self.dimension_weights = self.dimension_id.dimension_weights
            return {'domain': {'indicator_id': [('indicator_type', '=', self.dimension_id.dimension_type)]}}
        else:
            return {'domain': {'indicator_id': [('name', '=', 'False')]}}

    @api.onchange('indicator_id')
    def _onchange_indicator_id(self):
        """
        :return:
        """
        for res in self:
            if res.indicator_id:
                res.threshold_value = res.indicator_id.threshold_value
                res.target_value = res.indicator_id.target_value
                res.challenge_value = res.indicator_id.challenge_value
                res.assessment_criteria = res.indicator_id.assessment_criteria
                res.weights = res.indicator_id.weights
                res.notes = res.indicator_id.notes
                if res.indicator_id.indicator_type == 'bonus':
                    res.extra_end = res.indicator_id.extra_end
                elif res.indicator_id.indicator_type == 'deduction':
                    res.extra_end = res.indicator_id.deduction_end
                else:
                    res.extra_end = 0

