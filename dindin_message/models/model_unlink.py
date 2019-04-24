# -*- coding: utf-8 -*-
import logging
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

unlink_origin = models.BaseModel.unlink


@api.multi
def unlink(self):
    result = unlink_origin(self)
    check_model_send_message(self)
    return result


models.BaseModel.unlink = unlink


def check_model_send_message(self):
    for res in self:
        if res.id:
            model = res._name
            res_id = res.id
            check_result = self.env['dindin.message.template'].check_message_template(model, 'delete')
            if not check_result:
                return
            logging.info(">>>model:{}-记录id:{},进行发送模板消息".format(model, res_id))
            self.env['dindin.message.template'].send_message_template(model, res_id, 'delete')
