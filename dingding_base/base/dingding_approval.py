# -*- coding: utf-8 -*-
import logging
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def _commit_dingding_approval(self):
    """
    钉钉审批
    :param self:
    :return:
    """
    raise ValidationError("当前版本不支持，请升级专业版模块！")


def _restart_commit_approval(self):
    """
    重新提交钉钉审批
    :param self:
    :return:
    """
    raise ValidationError("当前版本不支持，请升级专业版模块！")


Model = models.Model
setattr(Model, 'commit_dingding_approval', _commit_dingding_approval)
setattr(Model, 'restart_commit_approval', _restart_commit_approval)
