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
        :param params: 员工user_id
        :return:
        """
        if provider == 'dingtalk_login':
            user = self.with_user(SUPERUSER_ID).search(['|', ('oauth_access_token', '=', params), ('oauth_uid', '=', params)], limit=1)
            if not user:
                raise AccessDenied()
            return (self.env.cr.dbname, user.login, str(params))
        else:
            return super(ResUsers, self).auth_oauth(provider, params)

    @api.model
    def _check_credentials(self, password, env):
        try:
            return super(ResUsers, self)._check_credentials(password, env)
        except AccessDenied:
            res = self.with_user(SUPERUSER_ID).search([('id', '=', self.env.uid), ('oauth_uid', '=', password)])
            if not res:
                raise
