# -*- coding: utf-8 -*-
import logging
import threading
from odoo import models, _, api
from odoo.http import request

_logger = logging.getLogger(__name__)


# ---创建---
origin_create = models.BaseModel.create


@api.model_create_multi
def create(self, values):
    result = origin_create(self, values)
    ir_model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
    company_id = self.env.user.company_id
    domain = [('model_id', '=', ir_model.id), ('company_id', '=', company_id.id),
              ('state', '=', 'open'), ('msg_opportunity', '=', 'normal'), ('message_timing', '=', 'save')]
    try:
        msg_config = request.env['dingtalk.message.config'].sudo().search(domain, limit=1)
    except Exception:
        msg_config = self.env['dingtalk.message.config'].sudo().search(domain, limit=1)
    if msg_config:
        for res in result:
            message_tool = self.env['dingtalk.message.tool']
            threading.Thread(target=message_tool.send_notice_message,
                             args=(msg_config.id, res._name, res.id, company_id)).start()
    return result


models.BaseModel.create = create


# ---修改---
origin_write = models.BaseModel.write


def write(self, vals):
    ir_model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
    company_id = self.env.user.company_id
    domain = [('model_id', '=', ir_model.id), ('company_id', '=', company_id.id),
              ('state', '=', 'open'), ('msg_opportunity', '=', 'normal'), ('message_timing', '=', 'write')]
    try:
        msg_config = request.env['dingtalk.message.config'].sudo().search(domain, limit=1)
    except Exception:
        msg_config = self.env['dingtalk.message.config'].sudo().search(domain, limit=1)
    if msg_config:
        message_tool = self.env['dingtalk.message.tool']
        if isinstance(vals, dict):
            threading.Thread(target=message_tool.send_notice_message,
                             args=(msg_config.id, self._name, self.id, company_id)).start()
        # if isinstance(vals, list):
        #     for res in vals:
        #         threading.Thread(target=message_tool.send_notice_message,
        #                          args=(msg_config.id, res._name, res.id, company_id)).start()
    return origin_write(self, vals)


models.BaseModel.write = write


# ---删除----
origin_unlink = models.BaseModel.unlink


@api.multi
def unlink(self):
    ir_model = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
    company_id = self.env.user.company_id
    domain = [('model_id', '=', ir_model.id), ('company_id', '=', company_id.id),
              ('state', '=', 'open'), ('msg_opportunity', '=', 'normal'), ('message_timing', '=', 'unlink')]
    try:
        msg_config = request.env['dingtalk.message.config'].sudo().search(domain, limit=1)
    except Exception:
        msg_config = self.env['dingtalk.message.config'].sudo().search(domain, limit=1)
    if msg_config:
        for res in self:
            message_tool = self.env['dingtalk.message.tool']
            threading.Thread(target=message_tool.send_notice_message,
                             args=(msg_config.id, res._name, res.id, company_id)).start()
    return origin_unlink(self)


models.BaseModel.unlink = unlink
