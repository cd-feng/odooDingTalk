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


class OaStockRequisition(models.Model):
    _name = 'oa.stock.requisition'
    _inherit = ['dingding.approval.main']
    _description = "货品调拨单"
    _rec_name = 'process_code'

    partner_id = fields.Many2one(comodel_name='res.partner', string=u'客户', required=True)
    req_date = fields.Date(string=u'日期', required=True)
    contact_id = fields.Many2one(comodel_name='res.partner', string=u'联系人', required=True)
    contact_phone = fields.Char(string='联系电话', required=True)
    shipping_address = fields.Char(string='收货地址')
    out_warehouse = fields.Many2one(comodel_name='stock.warehouse', string=u'转出仓库')
    out_location = fields.Many2one(comodel_name='stock.location', string=u'转出位置')
    ing_warehouse = fields.Many2one(comodel_name='stock.warehouse', string=u'转入仓库')
    ing_location = fields.Many2one(comodel_name='stock.location', string=u'转入位置')
    transfer_method = fields.Many2one(comodel_name='stock.transfer.method', string=u'调拨方式')
    bank_channel = fields.Many2one(comodel_name='stock.bank.channel', string=u'银行渠道')
    delivery_method = fields.Many2one(comodel_name='stock.delivery.method', string=u'货运方式')
    delivery_number = fields.Char(string='货运单号')
    line_ids = fields.One2many(comodel_name='oa.stock.requisition.line', inverse_name='requisition_id', string=u'调拨明细')

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
        fcv_list.append({'name': '客户', 'value': self.partner_id.name})
        fcv_list.append({'name': '日期', 'value': str(self.req_date)})
        fcv_list.append({'name': '单据编号', 'value': self.process_code})
        fcv_list.append({'name': '联系人', 'value': self.contact_id.name if self.contact_id else ''})
        fcv_list.append({'name': '联系电话', 'value': self.contact_phone if self.contact_phone else ''})
        fcv_list.append({'name': '收货地址', 'value': self.shipping_address if self.shipping_address else ''})
        fcv_list.append({'name': '发起人', 'value': self.originator_user_id.name})
        fcv_list.append({'name': '发起部门', 'value': [self.originator_dept_id.ding_id]})
        fcv_list.append({'name': '转出仓库', 'value': self.out_warehouse.name if self.out_warehouse else ''})
        fcv_list.append({'name': '转入仓库', 'value': self.ing_warehouse.name if self.ing_warehouse else ''})
        fcv_list.append({'name': '调拨方式', 'value': self.transfer_method.name if self.transfer_method else ''})
        fcv_list.append({'name': '银行渠道', 'value': self.bank_channel.name if self.bank_channel else ''})
        fcv_list.append({'name': '货运方式', 'value': self.delivery_method.name if self.delivery_method else ''})
        fcv_list.append({'name': '货运单号', 'value': self.delivery_number if self.delivery_number else ''})
        fcv_line = list()
        for line in self.line_ids:
            fcv_line_list = list()
            fcv_line_list.append({"name": "存货名称", "value": line.product_id.name})
            fcv_line_list.append({"name": "申请调拨数量", "value": line.approval_number_transfers})
            fcv_line_list.append({"name": "实际调拨数量", "value": line.actual_number_transfers})
            fcv_line_list.append({"name": "品控反馈", "value": line.control_feedback if self.control_feedback else ''})
            fcv_line.append(fcv_line_list)
        fcv_list.append({'name': '调拨明细', 'value': fcv_line})
        fcv_list.append({'name': '制单人', 'value': self.env.user.name})
        fcv_list.append({'name': '备注', 'value': self.reason_leave if self.reason_leave else ''})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, fcv_list)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')

    @api.model
    def create(self, values):
        values['process_code'] = self.env['ir.sequence'].sudo().next_by_code('oa.stock.requisition.code')
        return super(OaStockRequisition, self).create(values)


class OaStockRequisitionLine(models.Model):
    _name = 'oa.stock.requisition.line'
    _description = "货品调拨单列表"
    _rec_name = 'requisition_id'

    requisition_id = fields.Many2one(comodel_name='oa.stock.requisition', string=u'货品调拨单')
    product_id = fields.Many2one(comodel_name='product.template', string=u'存货名称', required=True)
    approval_number_transfers = fields.Float(string=u'申请调拨数量', required=True)
    actual_number_transfers = fields.Float(string=u'实际调拨数量', required=True)
    control_feedback = fields.Char(string=u'品控反馈')


