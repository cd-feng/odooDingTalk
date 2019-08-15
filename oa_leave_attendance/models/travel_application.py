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
import datetime
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class LeaveApplication(models.Model):
    _name = 'oa.travel.application'
    _inherit = ['dingding.approval.main']
    _description = "出差申请"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'申请人', required=True)
    sum_days = fields.Integer(string=u'总天数', compute='_compute_sum_days')
    line_ids = fields.One2many(comodel_name='oa.travel.application.line', inverse_name='oa_ta_id', string=u'出差列表')

    @api.multi
    def summit_approval(self):
        """
        提交到钉钉
        :return:
        """
        logging.info(">>>提交审批到钉钉...")
        # 获取审批流编码
        process_code = self._check_oa_model(self._name)
        # 表单参数
        form_component_values = list()
        form_component_values.append({'name': '申请人', 'value': self.emp_id.name})
        new_list = list()
        for line in self.line_ids:
            fcv_list = list()
            fcv_list.append({'name': '请假事由', 'value': line.ta_text})
            fcv_list.append({'name': '交通工具', 'value': line.ta_tool})
            fcv_list.append({'name': '单程往返', 'value': line.ta_type})
            fcv_list.append({'name': '出发城市', 'value': line.departure_city})
            fcv_list.append({'name': '目的城市', 'value': line.destination_city})
            fcv_list.append({'name': '开始日期', 'value': str(line.start_date)})
            fcv_list.append({'name': '结束日期', 'value': str(line.end_date)})
            fcv_list.append({'name': '时长（天）', 'value': str(line.ta_days)})
            fcv_list.append({'name': '备注', 'value': line.remarks})
            new_list.append(fcv_list)
        form_component_values.append({'name': '明细', 'value': new_list})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, fcv_list)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')

    @api.model
    def create(self, values):
        values['process_code'] = self.env['ir.sequence'].sudo().next_by_code('oa.travel.application.code')
        return super(LeaveApplication, self).create(values)

    @api.depends('line_ids')
    def _compute_sum_days(self):
        for res in self:
            t_day = 0
            for line in res.line_ids:
                t_day += line.ta_days
            res.sum_days = t_day


class LeaveApplicationLine(models.Model):
    _name = 'oa.travel.application.line'
    _description = u"出差申请列表"

    TATOOL = [
        ('飞机', '飞机'),
        ('火车', '火车'),
        ('汽车', '汽车'),
        ('船舶', '船舶'),
        ('其他', '其他'),
    ]

    sequence = fields.Integer(string=u'序号')
    start_date = fields.Date(string=u'开始日期', required=True)
    end_date = fields.Date(string=u'结束日期', required=True)
    departure_city = fields.Char(string='出发城市', required=True)
    destination_city = fields.Char(string='目的城市', required=True)
    ta_text = fields.Char(string=u'出差事由', required=True, help="请填写出差事由")
    ta_tool = fields.Selection(string=u'交通工具', selection=TATOOL, default='飞机', required=True)
    ta_type = fields.Selection(string=u'单程/往返', selection=[('单程', '单程'), ('往返', '往返'), ], default='单程')
    ta_days = fields.Integer(string=u'天数')
    remarks = fields.Text(string=u'备注')
    oa_ta_id = fields.Many2one(comodel_name='oa.travel.application', string=u'出差申请', ondelete='cascade')

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            start_date = datetime.datetime.strptime(str(self.start_date), "%Y-%m-%d")
            end_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d")
            self.ta_days = (end_date - start_date).days

