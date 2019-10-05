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

_logger = logging.getLogger(__name__)


class OvertimeApplication(models.Model):
    _name = 'oa.overtime.application'
    _inherit = ['dingding.approval.main']
    _description = "加班申请"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'申请人', required=True)
    start_date = fields.Datetime(string=u'开始时间', required=True)
    end_date = fields.Datetime(string=u'结束时间', required=True)
    duration = fields.Integer(string=u'时长(小时)')
    reason_leave = fields.Text(string=u'加班原因', required=True)

    def summit_approval(self):
        """
        提交到钉钉
        :return:
        """
        logging.info(">>>提交审批到钉钉...")
        # 获取审批流编码
        process_code = self._check_oa_model(self._name)
        # 表单参数
        fcv_list = list()
        fcv_list.append({'name': '申请人', 'value': self.emp_id.name})
        fcv_list.append({'name': '开始时间', 'value': str(self.start_date)})
        fcv_list.append({'name': '结束时间', 'value': str(self.end_date)})
        fcv_list.append({'name': '时长（小时）', 'value': str(self.duration)})
        fcv_list.append({'name': '加班原因', 'value': self.reason_leave})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, fcv_list)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')

    @api.model
    def create(self, values):
        values['process_code'] = self.env['ir.sequence'].sudo().next_by_code('oa.overtime.application.code')
        return super(OvertimeApplication, self).create(values)
