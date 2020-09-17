# -*- coding: utf-8 -*-
import logging
import threading
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, values):
        user = super(ResUsers, self).create(values)
        config = self.env['dingtalk.message.config'].is_new_user_send_msg()
        if config and user.employee:
            employee = None
            for emp in user.employee_ids:
                if emp.ding_id:
                    employee = emp
                    break
            if employee:
                msg_body = config.msg_body
                ding_id = employee.ding_id
                message_tool = self.env['dingtalk.message.tool']
                threading.Thread(target=message_tool.send_create_user_message,
                                 args=(employee.company_id, ding_id, msg_body, user.id)).start()
        return user
