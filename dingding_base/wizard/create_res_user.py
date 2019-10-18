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


class CreateResUser(models.TransientModel):
    _name = 'create.res.user'
    _description = "创建用户"

    @api.model
    def _default_domain(self):
        return [('user_id', '=', False)]

    employee_ids = fields.Many2many(comodel_name='hr.employee', string=u'员工', domain=_default_domain)
    groups = fields.Many2many(comodel_name='res.groups', string=u'分配权限')
    ttype = fields.Selection(string=u'账号类型', selection=[('phone', '工作手机'), ('email', '工作Email')], default='phone')

    @api.multi
    def create_user(self):
        """
        根据员工创建系统用户
        :return:
        """
        self.ensure_one()
        # 权限
        group_user = self.env.ref('base.group_user')[0]
        group_ids = list()
        for group in self.groups:
            group_ids.append(group.id)
        group_ids.append(group_user.id)
        for employee in self.employee_ids:
            values = {
                'active': True,
                "name": employee.name,
                'email': employee.work_email,
                'groups_id': [(6, 0, group_ids)],
                'ding_user_id': employee.ding_id,
                'ding_user_phone': employee.mobile_phone,
            }
            user_login = False
            if self.ttype == 'email':
                if not employee.work_email:
                    raise UserError("员工{}不存在工作邮箱，无法创建用户!".format(employee.name))
                values.update({'login': employee.work_email, "password": employee.work_email})
                user_login = employee.work_email
            else:
                if not employee.mobile_phone:
                    raise UserError("员工{}办公手机为空，无法创建用户!".format(employee.name))
                values.update({'login': employee.mobile_phone, "password": employee.mobile_phone})
                user_login = employee.mobile_phone
            domain = ['|', ('login', '=', employee.work_email), ('login', '=', employee.mobile_phone)]
            user = self.env['res.users'].sudo().search(domain, limit=1)
            if user:
                employee.sudo().write({'user_id': user.id})
            else:
                name_count = self.env['res.users'].sudo().search_count([('name', 'like', employee.name)])
                if name_count > 0:
                    user_name = employee.name + str(name_count + 1)
                    values['name'] = user_name
                user = self.env['res.users'].sudo().create(values)
                employee.sudo().write({'user_id': user.id})
                # 首次自动创建odoo用户后发送钉钉工作通知给该员工
                self.send_create_user_message(employee, user_login)

    @api.model
    def send_create_user_message(self, employee, user_login):
        """
        发送钉钉工作通知给该员工
        :param employee:
        :param user_name:
        :return:
        """
        # 创建odoo用户后发送钉钉工作通知给该员工
        msg = {
            'msgtype': 'text',
            'text': {
                "content": "您好：{},欢迎加入Odoo，登陆名：{}，初始密码：{}，请及时修改初始密码！您也可以使用工作台中(OdooERP应用)进行免密登录，请知悉！*_*".format(employee.name, user_login, user_login),
            }
        }
        return self.env['dingding.api.tools'].send_work_message(msg, employee.ding_id)


