# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DingTalkApprovalTemplate(models.Model):
    _name = 'dingtalk.approval.template'
    _description = "审批模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Html(string='图标', compute='_compute_icon_url')
    icon_avatar_url = fields.Text(string='图标url')
    process_code = fields.Char(string='模板唯一标识', required=True)
    url = fields.Text(string='模板跳转url')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company)

    @api.depends('icon_avatar_url')
    def _compute_icon_url(self):
        for res in self:
            if res.icon_avatar_url:
                res.icon_url = """<img src="{avatar_url}" width="60px" height="60px">""".format(avatar_url=res.icon_avatar_url)
            else:
                res.icon_url = False