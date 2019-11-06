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
        当选择了相关用户时，需要检查系统用户是否只对应一个员工
        :return:
        """
        if self.user_id:
            # 把员工的钉钉id和手机号写入到系统用户oauth
            if self.ding_id:
                users = self.env['res.users'].sudo().search([('ding_user_id', '=', self.ding_id)])
                if users:
                    users.sudo().write({'ding_user_id': False, 'ding_user_phone': False})
                self._cr.execute("""UPDATE res_users SET ding_user_id='{}',ding_user_phone='{}' WHERE id={}""".format(
                    self.ding_id, self.mobile_phone, self.user_id.id))
                self._cr.commit()


