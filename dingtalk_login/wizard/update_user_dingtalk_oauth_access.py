# -*- coding: utf-8 -*-

from odoo import models, exceptions


class UpdateDingtalkEmployeeAvatar(models.TransientModel):
    _name = 'update.user.dingtalk.oauth.access'
    _description = "批量修复员工用户Oauth"

    def on_update(self):
        """
        :return:
        """
        self.ensure_one()
        emp_count = 0
        for employee in self.env['hr.employee'].sudo().search([]):
            if employee.user_id and employee.ding_id:
                employee.user_id.sudo().write({
                    'oauth_uid': employee.ding_id,
                    'oauth_access_token': employee.ding_id
                })
                emp_count += 1
        return self.env.user.notify_success(message="修复完成，本次共修复{}条数据！".format(emp_count))

