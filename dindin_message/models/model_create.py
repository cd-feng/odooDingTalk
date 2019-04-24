# -*- coding: utf-8 -*-
import logging
from psycopg2._psycopg import ProgrammingError

from odoo import models, api

_logger = logging.getLogger(__name__)

create_origin = models.BaseModel.create


@api.model
@api.returns('self', lambda value: value.id)
def create(self, vals):
    record = create_origin(self, vals)
    check_model_send_message(self, record)
    return record


models.BaseModel.create = create


def check_model_send_message(self, record):
    model = self._name
    res_id = record.id
    try:
        check_result = self.env['dindin.message.template'].check_message_template(model, 'create')
    except ProgrammingError as e:
        return
    if not check_result:
        return
    logging.info(">>>model:{}-记录id:{},进行发送模板消息".format(model, res_id))
    self.env['dindin.message.template'].send_message_template(model, res_id, 'create')
