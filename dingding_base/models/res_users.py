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
import pypinyin
from odoo import api, fields, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = ['res.users']

    ding_user_phone = fields.Char(string='钉钉用户手机')
    ding_user_id = fields.Char(string='钉钉用户ID')

    @api.model
    def auth_oauth_dingtalk(self, provide_id, oauth_uid):
        if provide_id == 'dingtalk':
            user = self.sudo().search([('ding_user_id', '=', oauth_uid)])
        else:
            user = self.search([('oauth_provider_id', '=', provide_id), ('oauth_uid', '=', oauth_uid)])
        _logger.info("user: %s", user)
        if not user or len(user) > 1:
            return AccessDenied
        return (self.env.cr.dbname, user[0].login, oauth_uid)

    @api.model
    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            res = self.sudo().search([('id', '=', self.env.uid), ('oauth_uid', '=', password)])
            if not res:
                raise

    def create_user_by_employee(self, employee_id, password, active=True):
        """
        通过员工创建Odoo用户
        安装依赖 pypinyin:  pip install pypinyin
        """
        employee = self.env['hr.employee'].sudo().search([('id', '=', employee_id)])
        if employee:
            # 账号生成改为格式：姓名全拼+手机号末四位@企业邮箱域名
            email_name1 = pypinyin.slug(employee.name, separator='')  # 全拼
            # email_name1 = pypinyin.slug(employee.name, style=Style.FIRST_LETTER, separator='') # 首字母
            email_name2 = employee.mobile_phone[7:]  # 取手机号末四位
            email_name = email_name1 + email_name2
            # 这里后续可以加个开关，让管理员自己决定使用其他域名或企业邮箱域名
            url = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')
            if url:
                email_host = url
            else:
                email_host = 'dingtalk.com'
            email_count = len(self.search([('login', 'like', email_name)]).sudo())
            if email_count > 0:
                user = self.env['res.users'].sudo().search([('login', '=', email_name + '@' + email_host)])
                values = {
                    'user_id': user.id
                }
                employee.sudo().write(values)
            else:
                email = email_name + '@' + email_host
                # 获取不重复的姓名
                name = employee.name
                name_count = len(self.search([('name', 'like', name)]).sudo())
                if name_count > 0:
                    name = name + str(name_count + 1)
                # 创建Odoo用户
                values = {
                    'active': active,
                    "login": email,
                    "password": password,
                    "name": name,
                    'email': employee.work_email,
                    'groups_id': self.env.ref('base.group_user')
                }
                user = self.sudo().create(values)
                # 首次自动创建odoo用户后发送钉钉工作通知给该员工
                msg = {
                    'msgtype': 'text',  
                    'text': {
                        "content": "尊敬的{},欢迎加入odoo,您的登陆名为{}，初始登陆密码为{}，请登陆后及时修改密码！".format(name, email, password), 
                    }
                }
                self.env['dindin.work.message'].sudo().send_work_message(userstr=employee.ding_id, msg=msg)
                # 注册成功后，自动关联员工与用户
                values = {
                    'user_id': user.id
                }
                employee.sudo().write(values)
