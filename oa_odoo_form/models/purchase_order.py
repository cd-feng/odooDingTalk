# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):

    _name = 'purchase.order'
    _inherit = ["purchase.order", "odoo.dingding.form.base"]
    _auto = True

    state = fields.Selection(selection_add=[('ding_approval', u'钉钉审批')])

    @api.constrains('oa_state')
    def _constrains_oa_state_alert_state(self):
        """
        检查钉钉审批状态，当审批结束时修改单据状态为采购订单
        :return:
        """
        for res in self:
            if res.oa_state == '02':
                res.state = 'purchase'

    def send_to_dingding_approval(self):
        """
        提交到钉钉
        :return:
        """
        self.state = 'ding_approval'
        logging.info(">>>提交审批到钉钉...")
        # 获取审批模板编码
        process_code = self._check_oa_model(self._name)
        # 表单参数
        fcv_list = list()
        fcv_list.append({'name': '供应商', 'value': self.partner_id.name})
        fcv_list.append({'name': '单据日期', 'value': str(fields.datetime.strftime(self.date_order, '%Y-%m-%d'))})
        fcv_list.append({'name': '供应商参考', 'value': self.partner_ref})
        fcv_list.append({'name': '采购员', 'value': self.user_id.name})
        fcv_list.append({'name': '备注', 'value': ''})
        fcv_line = list()
        for line in self.order_line:
            fcv_line_list = list()
            fcv_line_list.append({"name": "产品", "value": line.product_id.name})
            fcv_line_list.append({"name": "说明", "value": line.name})
            fcv_line_list.append({"name": "计划日期", "value": str(
                fields.datetime.strftime(line.date_planned, '%Y-%m-%d'))})
            fcv_line_list.append({"name": "数量", "value": line.product_qty})
            fcv_line_list.append({"name": "单价", "value": line.price_unit})
            fcv_line_list.append({"name": "小计", "value": line.product_qty * line.price_unit})
            fcv_line.append(fcv_line_list)
        fcv_list.append({'name': '产品明细', 'value': fcv_line})
        # 发送单据信息至钉钉并接受审批实例id
        pid = self._summit_din_approval(process_code, fcv_list)
        self.write({'oa_state': '01', 'process_instance_id': pid})
        self.message_post(body=u"已提交至钉钉，请等待审批人进行审批！", message_type='notification')
