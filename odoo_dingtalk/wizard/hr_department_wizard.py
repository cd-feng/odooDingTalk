# -*- coding: utf-8 -*-
import logging
from odoo import models, exceptions, fields
_logger = logging.getLogger(__name__)


class DingtalkDepartment(models.TransientModel):
    _name = 'dingtalk.department.synchronous.wizard'
    _description = "钉钉部门同步向导"
    
    company_id = fields.Many2one('res.company', string="同步的公司", required=True, default=lambda self: self.env.company)
    
    def on_synchronous(self):
        """
        立即同步所有的部门数据
        :return:
        """
        try:
            department_data = self.env['hr.department'].request_dingtalk_department_data(self.company_id.id)
            self.env['hr.department'].update_dingtalk_department_data(department_data, self.company_id.id)
        except Exception as e:
            raise exceptions.ValidationError(f"同步钉钉部门数据失败: {e}")
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {
                'type': 'success', 'title': '同步数据结果',
                'message': "钉钉部门数据已同步完成!",
                'sticky': False, 'next': {'type': 'ir.actions.act_window_close'}
            }
        }