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


class OaFileType(models.Model):
    _name = 'oa.file.type'
    _description = "文件类别"

    name = fields.Char(string='类别名', required=True)
    text = fields.Char(string='描述')


class SealType(models.Model):
    _name = 'oa.seal.type'
    _description = "印章类别"

    name = fields.Char(string='类别名', required=True)
    text = fields.Char(string='描述')


class SealApplicationLine(models.Model):
    _name = 'oa.seal.application.line'
    _description = "用印申请子表"

    sequence = fields.Integer(string=u'序号')
    oa_seal_id = fields.Many2one(comodel_name='oa.seal.application', string=u'用印申请', ondelete='cascade')
    file_type = fields.Many2one(comodel_name='oa.file.type', string=u'文件类别', required=True)
    file_name = fields.Char(string='用印文件名称')
    file_number = fields.Integer(string=u'文件数量', default=1, required=True)
    remarks = fields.Char(string=u'备注')


class SealApplication(models.Model):
    _name = 'oa.seal.application'
    _inherit = ['dingding.approval.main']
    _description = "用印申请"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'用印人', required=True)
    dept_id = fields.Many2one(comodel_name='hr.department', string=u'用印部门', required=True)
    seal_date = fields.Date(string=u'用印日期', required=True)
    seal_type = fields.Many2one(comodel_name='oa.seal.type', string=u'印章类别', required=True)
    reason_leave = fields.Char(string=u'备注')
    line_ids = fields.One2many(comodel_name='oa.seal.application.line', inverse_name='oa_seal_id', string=u'文件明细')

    @api.onchange('emp_id')
    def onchange_emp_id(self):
        if self.emp_id:
            self.dept_id = self.emp_id.department_id.id

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
        form_component_values.append({'name': '用印人', 'value': self.emp_id.name})
        form_component_values.append({'name': '用印部门', 'value': self.dept_id.name})
        form_component_values.append({'name': '用印日期', 'value': str(self.seal_date)})
        form_component_values.append({'name': '印章类别', 'value': self.seal_type.name})
        form_component_values.append({'name': '备注', 'value': self.reason_leave if self.reason_leave else ''})
        new_list = list()
        for line in self.line_ids:
            fcv_list = list()
            fcv_list.append({'name': '文件类别', 'value': line.file_type.name})
            fcv_list.append({'name': '用印文件名称', 'value': line.file_name})
            fcv_list.append({'name': '文件数量', 'value': str(line.file_number)})
            fcv_list.append({'name': '备注', 'value': line.remarks if line.remarks else ''})
            new_list.append(fcv_list)
        form_component_values.append({'name': '文件明细', 'value': new_list})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, form_component_values)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')

    @api.model
    def create(self, values):
        values['process_code'] = self.env['ir.sequence'].sudo().next_by_code('oa.seal.application.code')
        return super(SealApplication, self).create(values)
