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


class ResignationApplication(models.Model):
    _name = 'oa.resignation.application'
    _inherit = ['dingding.approval.main']
    _description = "离职申请"
    _rec_name = 'emp_id'

    REASONTYPE = [
        ('家庭原因', '家庭原因'),
        ('个人原因', '个人原因'),
        ('发展原因', '发展原因'),
        ('合同到期不续签', '合同到期不续签'),
        ('协议解除', '协议解除'),
        ('无法胜任工作', '无法胜任工作'),
        ('经济型裁员', '经济型裁员'),
        ('严重违法违纪', '严重违法违纪'),
        ('其他', '其他'),
    ]

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'申请人', required=True)
    entry_date = fields.Date(string=u'入职日期')
    end_date = fields.Date(string=u'最后工作日')
    job_id = fields.Many2one(comodel_name='hr.job', string=u'职位')
    reason_type = fields.Selection(string=u'离职原因', selection=REASONTYPE, default='个人原因')
    reason_text = fields.Text(string=u'离职原因备注')

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
        fcv_list = list()
        fcv_list.append({'name': '申请人', 'value': self.emp_id.name})
        fcv_list.append({'name': '入职日期', 'value': str(self.entry_date)})
        fcv_list.append({'name': '最后工作日', 'value': str(self.end_date)})
        fcv_list.append({'name': '职位', 'value': self.job_id.name})
        fcv_list.append({'name': '离职原因', 'value': self.reason_type})
        fcv_list.append({'name': '离职原因备注', 'value': self.reason_text})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, fcv_list)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')

    @api.model
    def create(self, values):
        values['process_code'] = self.env['ir.sequence'].sudo().next_by_code('oa.resignation.application.code')
        return super(ResignationApplication, self).create(values)
