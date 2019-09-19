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


class DingDingCallbackList(models.Model):
    _name = 'dingding.callback.list'
    _description = "回调类型列表"
    _rec_name = 'name'

    ValueType = [
        ('00', '通讯录事件'),
        ('01', '群会话事件'),
        ('02', '签到事件'),
        ('03', '审批事件'),
    ]

    name = fields.Char(string='类型名')
    value = fields.Char(string='类型代码')
    call_back_url = fields.Char(string='回调地址函数')
    value_type = fields.Selection(string=u'事件分类', selection=ValueType, default='')

    _sql_constraints = [
        ('value_uniq', 'unique(value)', u'类型代码重复!'),
        ('name_uniq', 'unique(name)', u'类型名重复!'),
    ]
