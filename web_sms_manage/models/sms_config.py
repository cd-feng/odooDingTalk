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


class SmsConfig(models.Model):
    _description = '短信服务配置'
    _name = 'sms.service.config'
    _order = 'id'

    SmsType = [
        ('tencent', '腾讯云'),
        ('ali', '阿里云'),
    ]

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='名称')
    sms_type = fields.Selection(string=u'平台类型', selection=SmsType, default='tencent', required=True)
    app_id = fields.Char(string='AppID标识', required=True)
    app_key = fields.Char(string='App Key', help="App Key是用来校验短信发送请求合法性的密码", required=True)
    priority = fields.Integer(string=u'优先级(1-10)', default=3)
    code_length = fields.Integer(string=u'验证码长度', default=6)
    state = fields.Selection(string=u'状态', selection=[('close', '关闭'), ('open', '启用')], default='close')
    template_ids = fields.One2many(comodel_name='sms.service.template', inverse_name='service_id', string=u'短信模板')

    @api.multi
    def update_sms_status(self):
        """
        开启服务时，强制要检查模板列表是否满足条件；
        强制要求为：每个配置项必须包含"发送验证码模板、修改密码通知模板"
        :return:
        """
        for res in self:
            is_login = False
            is_change_pwd = False
            if res.state == 'close':
                for template in res.template_ids:
                    if template.used_for == 'login':
                        is_login = True
                    elif template.used_for == 'change_pwd':
                        is_change_pwd = True
                if is_login and is_change_pwd:
                    res.write({'state': 'open'})
                else:
                    raise UserError(u"短信模板数量不满足要求\r\n需要同时包含（'登录时发送验证码'、'修改密码通知模板'）服务模板！")
                res.write({'state': 'open'})
            else:
                res.write({'state': 'close'})


class SmsTemplate(models.Model):
    _description = '短信服务模板'
    _name = 'sms.service.template'
    _rec_name = 'service_id'
    _order = 'id'

    TemplateType = [
        ('login', '登录时发送验证码'),
        ('registered', '注册时发送验证码'),
        ('change_pwd', '修改密码通知模板'),
        ('close', '关闭'),
    ]

    name = fields.Char(string='说明', required=True)
    service_id = fields.Many2one(comodel_name='sms.service.config', string=u'短信服务')
    sign_name = fields.Char(string='签名名称', required=True)
    template_id = fields.Char(string='模板Id', required=True)
    timeout = fields.Integer(string='有效时长(分钟)', required=True, default=30)
    used_for = fields.Selection(string=u'模板用于', selection=TemplateType, required=True, default='close')
