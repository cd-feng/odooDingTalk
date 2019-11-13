# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkApprovalTemplateTran(models.TransientModel):
    _name = 'dingtalk.approval.template.tran'
    _description = "获取审批模板"

    def get_template(self):
        """
        获取审批模板
        :return:
        """
        self.ensure_one()
        client = dingtalk_api.get_client()
        offset = 0
        size = 100
        while True:
            try:
                result = client.post('topapi/process/listbyuserid', {'offset': offset, 'size': size})
            except Exception as e:
                raise UserError(e)
            if result.get('errcode') == 0:
                result = result.get('result')
                for process in result.get('process_list'):
                    data = {
                        'name': process.get('name'),
                        'icon_avatar_url': process.get('icon_url'),
                        'process_code': process.get('process_code'),
                        'url': process.get('url'),
                    }
                    template = self.env['dingtalk.approval.template'].search([('process_code', '=', process.get('process_code'))])
                    if template:
                        template.sudo().write(data)
                    else:
                        self.env['dingtalk.approval.template'].create(data)
                if result.get('next_cursor'):
                    offset += result.get('next_cursor')
                else:
                    break
            else:
                raise UserError('获取审批模板失败，详情为:{}'.format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}

