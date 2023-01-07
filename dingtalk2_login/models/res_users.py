# -*- coding: utf-8 -*-
import logging
from odoo import api, models
from odoo.exceptions import AccessDenied
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def auth_oauth(self, provider, params):
        """
        :param provider:
        :param params:
        :return:
        """
        if provider == 'dingtalk2_login':
            user = self.sudo().search([('oauth_uid', '=', params)], limit=1)
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
            res = self.sudo().search([('id', '=', self.env.uid), ('oauth_uid', '=', password)])
            if not res:
                raise
