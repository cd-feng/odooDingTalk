# -*- coding: utf-8 -*-

import base64
import logging
import requests
from odoo import api, fields, models, exceptions, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class UpdateDingtalkEmployeeAvatar(models.TransientModel):
    _name = 'update.dingtalk.employee.avatar'
    _description = "替换员工头像"

    company_ids = fields.Many2many('res.company', 'dingtalk_update_employee_avatar_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.company.id])])

    def on_update(self):
        """
        确认替换头像
        :return:
        """
        self.ensure_one()
        self.update_dingtalk_employee_avatar(self.company_ids.ids)

    def update_dingtalk_employee_avatar(self, company_ids):
        """
        执行替换操作
        :return:
        """
        for company_id in company_ids:
            company = self.env['res.company'].with_user(SUPERUSER_ID).search([('id', '=', company_id)], limit=1)
            domain = [('company_id', '=', company.id), ('ding_avatar_url', '!=', '')]
            employees = self.env['hr.employee'].sudo().search(domain)
            employees_len = len(employees)
            number = 1
            for employee in employees:
                _logger.info("%s >替换头像进度：%s / %s" % (company.name, number, employees_len))
                try:
                    binary_data = base64.b64encode(requests.get(employee.ding_avatar_url).content)
                    employee.write({'image_1920': binary_data, 'image_128': binary_data})
                    number += 1
                except Exception:
                    number += 1
                    continue
