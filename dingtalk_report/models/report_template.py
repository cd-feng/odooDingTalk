# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DingTalkReportTemplate(models.Model):
    _name = 'dingtalk.report.template'
    _description = "钉钉日志模板"

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Html(string='图标', compute='_compute_icon_url')
    icon_avatar_url = fields.Char(string='图标url')
    report_code = fields.Char(string='模板唯一标识', required=True)
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id)

    @api.depends('icon_avatar_url')
    def _compute_icon_url(self):
        for res in self:
            if res.icon_avatar_url:
                res.icon_url = """<img src="{avatar_url}" width="60px" height="60px">""".format(avatar_url=res.icon_avatar_url)
            else:
                res.icon_url = False

