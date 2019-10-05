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


class LeaveApplication(models.Model):
    _name = 'oa.leave.application'
    _inherit = ['dingding.approval.main']
    _description = "请假单"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'请假人', index=True, copy=False)
    leave_type = fields.Many2one(comodel_name='oa.leave.type', string=u'请假类型')
    start_date = fields.Date(string=u'开始时间')
    end_date = fields.Date(string=u'结束时间')
    reason_leave = fields.Text(string=u'请假事由')
    make_copy_users = fields.Many2many(
        string=u'抄送人',
        comodel_name='hr.employee',
        relation='oa_leave_application_employee_rel',
        column1='leave_id',
        column2='emp_id',
    )

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
        fcv_list.append({'name': '请假人', 'value': self.emp_id.name})
        fcv_list.append({'name': '请假类型', 'value': self.leave_type.name})
        fcv_list.append({'name': '开始时间', 'value': str(self.start_date)})
        fcv_list.append({'name': '结束时间', 'value': str(self.end_date)})
        fcv_list.append({'name': '请假事由', 'value': self.reason_leave})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, fcv_list)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')

    @api.model
    def create(self, values):
        values['process_code'] = self.env['ir.sequence'].sudo().next_by_code('oa.leave.application.code')
        return super(LeaveApplication, self).create(values)
