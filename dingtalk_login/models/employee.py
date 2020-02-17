# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('user_id')
    def _constrains_dingtalk_user_id(self):
        """
        当修改关联用户时，将员工的钉钉ID写入到系统用户中
        :return:
        """
        if self.user_id and self.ding_id:
            # 把员工的钉钉id和手机号写入到系统用户oauth
            users = self.env['res.users'].sudo().search([('ding_user_id', '=', self.ding_id)])
            if users:
                users.sudo().write({'ding_user_id': False, 'ding_user_phone': False})
            self.user_id.sudo().write({
                'ding_user_id': self.ding_id,
                'ding_user_phone': self.mobile_phone,
            })