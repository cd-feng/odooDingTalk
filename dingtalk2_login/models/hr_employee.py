# -*- coding: utf-8 -*-
from odoo import api, models


class SyncEmployee(models.TransientModel):
    _inherit = 'dingtalk2.syn.employee'

    @api.model
    def create_dingtalk_user(self, employee_ids):
        """
        根据创建的员工再次创建系统用户
        """
        oauth_id = self.env.ref('dingtalk2_login.dingtalk2_login_auth_oauth').sudo()
        for employee_id in employee_ids:
            user_data = {
                'name': employee_id.name,
                'login': employee_id.work_email or employee_id.ding_org_email or employee_id.mobile_phone or employee_id.work_phone,
                'oauth_uid': employee_id.ding_unionid,
                'oauth_provider_id': oauth_id.id,
            }
            if employee_id.user_id:
                user_id = employee_id.user_id
                del user_data['login']
                employee_id.user_id.write(user_data)
            else:
                user_id = self.env['res.users'].sudo().create(user_data)
            employee_id.write({'user_id': user_id.id})
