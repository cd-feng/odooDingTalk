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

import base64
import json
import logging
import requests
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GetProcessInstance(models.TransientModel):
    _name = 'oa.get.process.instance'
    _description = "获取审批实例"

    oa_madel = fields.Many2one(comodel_name='dingding.approval.template', string=u'审批模型')
    start_time = fields.Datetime(string=u'开始时间')
    end_time = fields.Datetime(string=u'结束时间')

    @api.multi
    def get_process_list(self):
        """
        根据选择的审批模型批量获取实例id，再通过实例id去获取实例详情
        :return:
        """
        self.ensure_one()
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('processinstance_listids')
        size = 20
        cursor = 0
        start_time = str(self.env['dingding.api.tools'].datetime_to_stamp(self.start_time))[:13]
        end_time = str(self.env['dingding.api.tools'].datetime_to_stamp(self.end_time))[:13]
        process_list = list()    # 实例数组
        while True:
            data = {
                'process_code': self.oa_madel.process_code,
                'start_time': start_time,
                'end_time': end_time,
                'size': size,
                'cursor': cursor,
            }
            result = self.env['dingding.api.tools'].send_post_request(url, token, data, 15)
            r_result = result.get('result')
            for arr in r_result.get('list'):
                process_list.append(arr)
            if 'next_cursor' not in r_result:
                break
            cursor = r_result.get('next_cursor')
        print(process_list)
