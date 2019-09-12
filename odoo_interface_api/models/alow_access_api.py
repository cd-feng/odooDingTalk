# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AlowAccessApi(models.Model):
    _name = 'api.alow.access'
    _description = "放行应用"
    _rec_name = 'name'
    _order = 'id'

    SystemType = [
        ('wx_xcx', '微信小程序'),
        ('wx_gzh', '微信公众号'),
        ('dd_xcx', '钉钉小程序'),
        ('other', '其他应用'),
    ]
    name = fields.Char(string='名称', index=True)
    system_type = fields.Selection(string=u'系统类型', selection=SystemType, default='wx_xcx', index=True)
    app_id = fields.Char(string='应用ID(应用标识)', help="用于odoo识别该应用是否允许获取api，外部系统需在请求时传递本参数", index=True)
    active = fields.Boolean(string=u'有效', default=True, index=True)

    _sql_constraints = [
        ('app_id_uniq', 'UNIQUE (app_id)', '该应用ID已存在，请更换！'),
    ]