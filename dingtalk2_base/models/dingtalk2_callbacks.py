# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, SUPERUSER_ID, api
_logger = logging.getLogger(__name__)


class Dingtalk2Callbacks(models.AbstractModel):
    _name = 'dingtalk2.callbacks'
    _description = "处理钉钉回调模型"

    @api.model
    def dingtalk_msg_callback(self, encrypt_result, company_id):
        """
        接受钉钉消息回调
        :param encrypt_result: 解密后的消息
        :param company_id: 当前公司id
        :return:
        """
        with self.pool.cursor() as cr:
            self = self.with_env(self.env(cr=cr))
            res_company = self.env['res.company'].with_user(SUPERUSER_ID).search([('id', '=', company_id)])
            try:
                result_index = encrypt_result.rfind('}')
                new_encrypt_result = encrypt_result[0:result_index + 1]
                encrypt_result = json.loads(new_encrypt_result.encode('utf-8'))
            except Exception:
                try:
                    encrypt_result = json.loads(encrypt_result.encode('utf-8'))
                except Exception:
                    return
            return self.with_user(SUPERUSER_ID).deal_dingtalk_msg(encrypt_result.get('EventType'), encrypt_result, res_company)

    @api.model
    def deal_dingtalk_msg(self, event_type, encrypt_result, res_company):
        """
        处理回调的消息
        :param event_type     钉钉回调类型
        :param encrypt_result 钉钉回调的消息内容
        :param res_company    回调的公司实例
        """
        _logger.info("> dingtalk callback msg：[{}]__>{}".format(res_company.name, event_type))
        return True
