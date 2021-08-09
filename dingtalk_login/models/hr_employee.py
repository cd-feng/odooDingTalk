# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('user_id')
    def _constrains_user_id(self):
        """
        当修改关联用户时，将员工的钉钉ID写入到系统用户中
        :return:
        """
        for res in self:
            if res.user_id and res.ding_id:
                users = self.env['res.users'].with_user(SUPERUSER_ID).search(
                    [('oauth_uid', '=', res.ding_id), ('company_id', '=', res.company_id.id)])
                if users:
                    users.with_user(SUPERUSER_ID).write({'oauth_uid': False})
                res.user_id.sudo().write({'oauth_uid': res.ding_id})
