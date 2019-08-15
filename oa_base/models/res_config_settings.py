# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # 安装钉钉模块
    module_oa_leave_attendance = fields.Boolean('钉钉审批-出勤休假')
    module_oa_personnel_admin = fields.Boolean('钉钉审批-行政人事')
