# -*- coding: utf-8 -*-

import logging
from odoo import api, models, SUPERUSER_ID
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def auth_oauth(self, provider, params):
        """
        :param provider:
        :param params:  员工id
        :return:
        """
        if provider == 'dingtalk_login':
            user = self.sudo().search([('oauth_access_token', '=', params)], limit=1)
            if not user:
                return False
            return (self.env.cr.dbname, user.login, str(params))
        else:
            return super(ResUsers, self).auth_oauth(provider, params)
