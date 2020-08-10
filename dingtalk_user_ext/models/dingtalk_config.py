# -*- coding: utf-8 -*-
from odoo import models, fields


class DingTalkConfig(models.Model):
    _inherit = 'dingtalk.mc.config'

    is_auto_create_user = fields.Boolean(string="自动创建系统用户？", default=False,
                                         help='开启自动创建系统用户后，系统将会在收到钉钉回调通知后，立即创建一个属于该员工的系统用户！')

    def set_default_user_groups(self):
        """
        设置默认系统用户权限
        :return:
        """
        action = self.env.ref('base.action_res_users').read()[0]
        action['res_id'] = self.env.ref('base.default_user').id
        action['views'] = [[self.env.ref('base.view_users_form').id, 'form']]
        return action
