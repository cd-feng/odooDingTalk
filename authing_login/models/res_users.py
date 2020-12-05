# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api
from authing.authing import Authing
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AuthingUsers(models.TransientModel):
    _name = 'get.authing.users'
    _description = '获取用户列表'

    def get_authing_users(self):
        """
        从Authing服务器中获取所有用户
        :return:
        """
        self.ensure_one()
        authing_client_id = self.env['ir.config_parameter'].sudo().get_param('authing_login.default_authing_client_id')
        authing_secret = self.env['ir.config_parameter'].sudo().get_param('authing_login.default_authing_secret')
        if not authing_client_id or not authing_secret:
            raise UserError("请先配置Authing必要的参数！")
        # 获取默认权限
        authing_group_id = self.env['ir.config_parameter'].sudo().get_param('authing_login.default_authing_group_id')
        groups = self.env['authing.user.groups'].search([('id', '=', authing_group_id)], limit=1)
        group_list = list()
        if not groups:
            group_list.append(self.env.ref('base.group_user').id)
        else:
            group_list = groups.groups_ids.ids

        authing = Authing(authing_client_id.replace(' ', ''), authing_secret.replace(' ', ''))
        page = 0
        count = 100
        users_sum = authing.list(page=page, count=count)
        user_list = list()
        provider = self.env['auth.oauth.provider'].sudo().search([('name', '=', 'Authing')], limit=1)
        total_count = users_sum.get('totalCount')
        new_page = int(total_count / count)
        while True:
            page += 1
            authing_users = authing.list(page=page, count=count)
            for line in authing_users.get('list'):
                users = self.env['res.users'].search([('oauth_uid', '=', line['_id'])])
                if users:
                    users.sudo().write({
                        'name': line['username'] or line['nickname'],
                        'login': line['email'] or line['username'],
                        'oauth_provider_id': provider.id or False,
                    })
                else:
                    user_list.append({
                        'name': line['username'] or line['nickname'],
                        'login': line['email'] or line['username'],
                        'groups_id': [(6, 0, group_list)],
                        'oauth_provider_id': provider.id or False,
                        'oauth_uid': line['_id'],
                    })
            if page >= new_page:
                break
        if len(user_list) > 0:
            self.env['res.users'].sudo().create(user_list)
        return {'type': 'ir.actions.client', 'tag': 'reload'}


