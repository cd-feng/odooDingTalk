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
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)
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

    @api.onchange('state')
    @api.constrains('state')
    def _update_line_state(self):
        """
        当当前单据状态发生变化时，将状态信息写入到子表
        :return:
        """
        for res in self:
            for line in res.line_ids:
                line.state = res.state

    
    def return_setting(self):
        """
        回到初始状态
        :return:
        """
        for res in self:
            res.state = 'setting'

    
    def summit_performance(self):
        """
        提交目标
        :return:
        """
        for res in self:
            # 检查权重是否等于100
            dimension_weights = 0
            for line in res.line_ids:
                dimension_weights += line.dimension_weights
            if dimension_weights != 100:
                raise UserError("您的考评项目权重小于或大于100，请纠正！")
            res.state = 'executing'

    
    def summit_rating(self):
        """
        提交评分
        :return:
        """
        for res in self:
            for line in res.line_ids:
                for library in line.library_ids:
                    if library.employee_rating <= 0:
                        raise UserError("您还有未评分项未完成或评分值不正确，请纠正！")
            res.state = 'close'

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

    
    def unlink(self):
        """
        删除方法
        :return:
        """
        for res in self:
            if res.state != 'setting':
                raise UserError("已在进行中的流程不允许删除！")
        return super(PerformanceAssessment, self).unlink()


class PerformanceAssessmentLine(models.Model):
    _name = 'performance.assessment.line'
    _description = "绩效考评项目"
    _rec_name = 'dimension_id'

    PerState = [
        ('setting', '目标制定'),
        ('executing', '执行中'),
        ('evaluation', '自评'),
        ('close', '结束'),
    ]

    performance_id = fields.Many2one(comodel_name='performance.assessment', string=u'绩效考评')
    state = fields.Selection(string=u'考评状态', selection=PerState, default='setting')
    sequence = fields.Integer(string=u'序号')
    dimension_id = fields.Many2one(comodel_name='performance.dimension.manage', string=u'考评维度', required=True)
    dimension_weights = fields.Integer(string=u'权重')
    library_ids = fields.One2many('performance.assessment.line.library', 'assessment_line_id', string=u'考评指标')
    assessment_result = fields.Integer(string=u'考核结果', compute='_compute_result', store=True)
    performance_grade_id = fields.Many2one('performance.grade.manage', string=u'绩效等级', compute='_compute_result', store=True)

    @api.onchange('dimension_id')
    def _onchange_dimension_id(self):
        """
        :return:
        """
        if self.dimension_id:
            self.library_ids = False
            self.dimension_weights = self.dimension_id.dimension_weights

    @api.onchange('state')
    @api.constrains('state')
    def _update_line_state(self):
        """
        当当前单据状态发生变化时，将状态信息写入到子表
        :return:
        """
        for res in self:
            for library in res.library_ids:
                library.state = res.state

    @api.depends('library_ids.employee_rating')
    def _compute_result(self):
        """
        计算结果
        :return:
        """
        for res in self:
            if res.state == 'evaluation':
                result = 0
                for library in res.library_ids:
                    result += library.employee_rating
                res.assessment_result = result
                grades = self.env['performance.grade.manage'].sudo().search([('active', '=', True)])
                for grade in grades:
                    if grade.interval_from <= result < grade.interval_end:
                        res.performance_grade_id = grade.id
                        break


class PerformanceAssessmentLineLibrary(models.Model):
    _name = 'performance.assessment.line.library'
    _description = "考评指标"
    _rec_name = 'indicator_id'
    PerState = [
        ('setting', '目标制定'),
        ('executing', '执行中'),
        ('evaluation', '自评'),
        ('close', '结束'),
    ]

    assessment_line_id = fields.Many2one(comodel_name='performance.assessment.line', string=u'绩效考评项目')
    state = fields.Selection(string=u'考评状态', selection=PerState, default='setting')
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
    employee_rating = fields.Integer(string=u'员工评分')
    employee_notes = fields.Text(string=u'评分说明')

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

