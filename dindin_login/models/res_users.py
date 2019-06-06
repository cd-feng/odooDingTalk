# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models

import pypinyin
from pypinyin import Style

_logger = logging.getLogger(__name__)


class InheritResUsers(models.Model):
    _inherit = ['res.users']

    @api.model
    def _get_defaultdin_pwd(self):
        return base64.b64encode('123456'.encode('utf-8'))

    din_password = fields.Char(string='钉钉登录密码', default=_get_defaultdin_pwd, size=64)

    def _set_password(self):
        for user in self:
            user.sudo().write({'din_password': base64.b64encode(user.password.encode('utf-8'))})
        super(InheritResUsers, self)._set_password()

    def create_user_by_employee(self, employee_id, password, active=True):
        """
        通过员工创建Odoo用户
        安装依赖 pypinyin:  pip install pypinyin
        """
        employee = self.env['hr.employee'].sudo().search([('id', '=', employee_id)])
        if employee:
            # 账号生成改为格式：姓名全拼+手机号末四位@企业邮箱域名
            email_name1 = pypinyin.slug(employee.name, separator='') #全拼
            # email_name1 = pypinyin.slug(employee.name, style=Style.FIRST_LETTER, separator='') #首字母
            email_name2 = employee.mobile_phone[7:] #取手机号末四位
            email_name = email_name1 + email_name2
            
            #这里后续可以加个开关，让管理员自己决定使用其他域名或企业邮箱域名
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

                # 注册成功后，自动关联员工与用户
                values = {
                    'user_id': user.id
                }
                employee.sudo().write(values)