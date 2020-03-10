# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    INTERVALTYPE = [('days', '天'), ('weeks', '周'), ('months', '月')]

    dt_attendance_interval = fields.Boolean(string="定时获取考勤信息", config_parameter='dingtalk_base.dt_attendance_interval')
    dt_attendance_interval_type = fields.Selection(string=u'执行间隔', selection=INTERVALTYPE, config_parameter='dingtalk_base.dt_attendance_interval_type')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.dt_attendance_interval:
            domain = [('state', '=', 'code'), ('code', '=', "env['dingtalk.attendance.cron.task'].start_task()")]
            cron = self.env['ir.cron'].sudo().search(domain)
            if not cron:
                self.env['ir.cron'].create({
                    'name': "钉钉-定时拉取员工考勤打卡结果",
                    'model_id': self.env['ir.model'].sudo().search([('model', '=', 'dingtalk.attendance.cron.task')], limit=1).id,
                    'user_id': 1,
                    'interval_number': 1,
                    'interval_type': self.dt_attendance_interval_type or 'days',
                    'numbercall': -1,
                    'doall': False,
                    'state': 'code',
                    'code': "env['dingtalk.attendance.cron.task'].start_task()",
                })
            else:
                cron.write({
                    'interval_type': self.dt_attendance_interval_type or 'days',
                })
        else:
            domain = [('state', '=', 'code'), ('code', '=', "env['dingtalk.attendance.cron.task'].start_task()")]
            self.env['ir.cron'].sudo().search(domain).unlink()
