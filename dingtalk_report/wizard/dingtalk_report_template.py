# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkReportTemplateTran(models.TransientModel):
    _name = 'dingtalk.report.template.tran'
    _description = "获取钉钉日志模板"

    def get_template(self):
        """
        获取所有日志模板
        :return:
        """
        self.ensure_one()
        client = dingtalk_api.get_client(self)
        offset = 0
        size = 100
        while True:
            try:
                result = client.post('topapi/report/template/listbyuserid', {'offset': offset, 'size': size})
            except Exception as e:
                raise UserError(e)
            if result.get('errcode') == 0:
                result = result.get('result')
                for template_list in result.get('template_list'):
                    data = {
                        'name': template_list.get('name'),
                        'icon_avatar_url': template_list.get('icon_url'),
                        'report_code': template_list.get('report_code'),
                        'url': template_list.get('url'),
                    }
                    template = self.env['dingtalk.report.template'].search([('report_code', '=', template_list.get('report_code'))])
                    if template:
                        template.write(data)
                    else:
                        self.env['dingtalk.report.template'].create(data)
                if result.get('next_cursor'):
                    offset += result.get('next_cursor')
                else:
                    break
            else:
                raise UserError('获取获取所有日志模板失败，详情为:{}'.format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}

