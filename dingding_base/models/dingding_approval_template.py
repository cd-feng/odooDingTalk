# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingApprovalTemplate(models.Model):
    _name = 'dingding.approval.template'
    _description = "审批模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    process_code = fields.Char(string='模板唯一标识', required=True)
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_template(self):
        """获取审批模板"""
        logging.info(">>>获取审批模板...")
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('process_listbyuserid')
        data = {
            'offset': 0,
            'size': 100,
        }
        result = self.env['dingding.api.tools'].send_post_request(url, token, data, 2)
        if result.get('errcode') == 0:
            d_res = result.get('result')
            for process in d_res.get('process_list'):
                data = {
                    'name': process.get('name'),
                    'icon_url': process.get('icon_url'),
                    'process_code': process.get('process_code'),
                    'url': process.get('url'),
                }
                template = self.env['dingding.approval.template'].search(
                    [('process_code', '=', process.get('process_code'))])
                if template:
                    template.write(data)
                else:
                    self.env['dingding.approval.template'].create(data)
        else:
            raise UserError('获取审批模板失败，详情为:{}'.format(result.get('errmsg')))
        logging.info(">>>获取审批模板结束...")
