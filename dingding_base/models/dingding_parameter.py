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

_logger = logging.getLogger(__name__)


class DingDingParameter(models.Model):
    _description = '系统参数列表'
    _name = 'dingding.parameter'

    name = fields.Char(string='名称')
    key = fields.Char(string='key值')
    value = fields.Char(string='参数值')

    _sql_constraints = [
        ('key_uniq', 'unique(key)', u'系统参数中key值不允许重复!'),
    ]

    @api.model
    def get_parameter_value(self, key):
        """
        根据key获取对应的value
        :param key: string
        :return:
        """
        parameter = self.search([('key', '=', key)])
        return parameter.value if parameter and parameter.value else False

    @api.model
    def get_parameter_value_and_token(self, key):
        """
        返回指定value和token
        :param key:
        :return:
        """
        parameter = self.get_parameter_value(key)
        token = self.search([('key', '=', 'token')]).value
        return parameter, token
