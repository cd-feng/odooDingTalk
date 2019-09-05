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
import datetime

_logger = logging.getLogger(__name__)


class SmsVerificationRecord(models.Model):
    _description = '短信验证码记录'
    _name = 'sms.verification.record'
    _rec_name = 'phone'
    _order = 'id'

    service_id = fields.Many2one(comodel_name='sms.service.config', string=u'短信服务平台')
    user_id = fields.Many2one(comodel_name='res.users', string=u'用户')
    phone = fields.Char(string='手机号码')
    sid = fields.Char(string='短信标识 ID')
    code = fields.Char(string='验证码')
    send_time = fields.Datetime(string=u'发送时间')
    end_time = fields.Datetime(string=u'截至时间')
    timeout = fields.Integer(string='有效时长(分钟)', required=True, default=30)
    state = fields.Selection(string=u'状态', selection=[('normal', '未使用'), ('invalid', '已使用'), ], default='normal')

    @api.constrains('code')
    def constrains_sms_code(self):
        """
        检查验证码的时候计算截止的日期
        :return:
        """
        for res in self:
            res.write({
                'send_time': datetime.datetime.now(),
                'end_time': datetime.datetime.now() + datetime.timedelta(minutes=res.timeout)
            })
