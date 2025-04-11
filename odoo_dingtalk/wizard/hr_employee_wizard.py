# -*- coding: utf-8 -*-
import logging
import threading
from odoo import models, api, fields, exceptions

_logger = logging.getLogger(__name__)
SYNCHRONOUS_EMP_STATUS = False


class DingtalkEmployeeWizard(models.TransientModel):
    _name = 'dingtalk.employee.synchronous.wizard'
    _description = "钉钉员工同步向导"

    company_id = fields.Many2one('res.company', string="公司", required=True, default=lambda self: self.env.company)

    def on_synchronous(self):
        """
        立即同步按钮
        :return:
        """
        global SYNCHRONOUS_EMP_STATUS
        if SYNCHRONOUS_EMP_STATUS:
            raise exceptions.UserError("正在后台同步数据，请稍后在人员档案中查看数据.")
        SYNCHRONOUS_EMP_STATUS = True
        threading.Thread(target=self.synchronous_department_emp, args=[self.env.user.id, self.company_id.id]).start()
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {
                'type': 'success', 'title': '钉钉同步通知',
                'message': f"系统正在后台同步员工数据，请耐心等待执行完成.",
                'sticky': False, 'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    @api.model
    def synchronous_department_emp(self, uid, company_id):
        """
        执行同步操作
        """
        global SYNCHRONOUS_EMP_STATUS
        with self.pool.cursor() as new_cr:
            self = self.with_env(self.env(cr=new_cr, su=True))
            employee_model = self.env['hr.employee'].sudo()
            try:
                employee_model.request_dingtalk_employee_data(company_id)
                threading.Thread(target=employee_model.create_employee_user, args=[company_id]).start()
            except Exception as e:
                raise exceptions.ValidationError(f"同步钉钉员工数据失败：{e}")
            finally:
                SYNCHRONOUS_EMP_STATUS = False
