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

import json
import logging
import time
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    wx_openid = fields.Char(string='微信OpenId', readonly=True, index=True)
    wx_nick_name = fields.Char(string='微信昵称')
    wx_avatar_url = fields.Text(string='微信头像Url')
    number = fields.Char(string='员工编号')
    education = fields.Char(string='学历')
    nationality = fields.Char(string='民族')
    birthplace = fields.Char(string='籍贯')
    serve_start_date = fields.Date(string=u'任职日期')

    def clear_wx_openid(self):
        """
        清除微信openid、昵称、头像url
        :return:
        """
        self.write({
            'wx_openid': '',
            'wx_nick_name': '',
            'wx_avatar_url': '',
        })
