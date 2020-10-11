# -*- coding: utf-8 -*-
import logging
import threading
from odoo import api, fields, models, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class DingTalkMcSynchronous(models.TransientModel):
    _inherit = 'dingtalk.mc.synchronous'

    def synchronous_dingtalk_employee(self, repeat_type=None):
        """
        同步部门员工列表
        :param repeat_type:
        :return:
        """
        super(DingTalkMcSynchronous, self).synchronous_dingtalk_employee(repeat_type)
        for company in self.company_ids:
            config = self.env['dingtalk.mc.config'].with_user(SUPERUSER_ID).search([('company_id', '=', company.id)], limit=1)
            if config.is_auto_create_user:
                threading.Thread(target=self.create_employee_user, args=company).start()
        return True

    @api.model
    def create_employee_user(self, company):
        """
        :param company: 公司
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                domain = [('user_id', '=', False), ('ding_id', '!=', ''), ('company_id', '=', company.id)]
                employees = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain)
                # 封装消息
                message_list = list()
                for employee in employees:
                    values = {
                        'active': True,
                        'company_id': company.id,
                        "name": employee.name,
                        'email': employee.work_email,
                        'ding_user_id': employee.ding_id,
                        'ding_user_phone': employee.mobile_phone,
                        'employee': True,
                        'employee_ids': [(6, 0, [employee.id])],
                    }
                    if employee.work_email:
                        values.update({'login': employee.work_email, "password": employee.work_email})
                    elif employee.mobile_phone:
                        values.update({'login': employee.mobile_phone, "password": employee.mobile_phone})
                    else:
                        continue
                    domain = ['|', ('login', '=', employee.work_email), ('login', '=', employee.mobile_phone)]
                    user = self.env['res.users'].with_user(SUPERUSER_ID).search(domain, limit=1)
                    if user:
                        employee.write({'user_id': user.id})
                    else:
                        name_count = self.env['res.users'].with_user(SUPERUSER_ID).search_count([('name', 'like', employee.name)])
                        if name_count > 0:
                            user_name = employee.name + str(name_count + 1)
                            values['name'] = user_name
                        user = self.env['res.users'].with_user(SUPERUSER_ID).create(values)
                        employee.write({'user_id': user.id})
                    message_list.append({'ding_id': employee.ding_id, 'values': values})
