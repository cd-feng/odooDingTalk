# -*- coding: utf-8 -*-

import logging
from odoo import models, api
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


Model = models.Model
original_setup_base = Model._setup_base


@api.model
def _setup_base(self):
    original_setup_base(self)
    setup_approval_state_fields(self)


def setup_approval_state_fields(self):
    """
    钉钉审批字段
    :param self:
    :return:
    """
    return dingtalk_api.setup_approval_state_fields(self)


Model._setup_base = _setup_base

create_origin = models.BaseModel.create

write_origin = models.BaseModel.write


def write(self, vals):
    dingtalk_approval_write(self, vals)
    return write_origin(self, vals)


def dingtalk_approval_write(self, vals):
    """不允许单据修改"""
    return dingtalk_api.dingtalk_approval_write(self, vals)


models.BaseModel.write = write

unlink_origin = models.BaseModel.unlink


def unlink(self):
    dingtalk_approval_unlink(self)
    return unlink_origin(self)


def dingtalk_approval_unlink(self):
    """非草稿单据不允许删除"""
    return dingtalk_api.dingtalk_approval_unlink(self)


models.BaseModel.unlink = unlink
