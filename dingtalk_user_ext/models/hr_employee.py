# -*- coding: utf-8 -*-
import logging
import threading
from odoo import api, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_employee_info(self, user_id, event_type, company):
        """
        获取用户详情执行函数
        :param user_id:
        :param event_type:
        :param company:
        :return:
        """
        res = super(HrEmployee, self).get_employee_info(user_id, event_type, company)
        config = self.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)], limit=1)
        if config.is_auto_create_user:
            synchronous = self.env['dingtalk.mc.synchronous']
            threading.Thread(target=synchronous.create_employee_user, args=company).start()
        return res
