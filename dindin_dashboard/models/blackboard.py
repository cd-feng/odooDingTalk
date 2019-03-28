# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class DinDinBlackboard(models.TransientModel):
    _description = '获取公告信息'
    _name = 'dindin.blackboard'

    @api.model
    def get_blackboard_by_user(self):
        """
        根据当前用户获取公告信息
        :return:
        """
        logging.info(self.env.user.name)