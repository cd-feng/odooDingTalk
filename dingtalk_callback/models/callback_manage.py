# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
import random
import string
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkCallback(models.Model):
    _name = 'dingtalk.callback.manage'
    _inherit = ['mail.thread']
    _description = "钉钉回调管理"
    _rec_name = 'value_type'

    @api.model
    def _get_default_aes_key(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 43))

    @api.model
    def _get_default_token(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 10))

    @api.model
    def _get_default_localhost(self):
        return "{}web/dingtalk/callback/do".format(request.httprequest.host_url)

    ValueType = [
        ('all', '所有事件'),
        ('00', '通讯录事件'),
        ('01', '群会话事件'),
        ('02', '签到事件'),
        ('03', '审批事件'),
    ]

    value_type = fields.Selection(string=u'注册事件类型', selection=ValueType, default='all', copy=False, required=True)
    token = fields.Char(string='Token', default=_get_default_token, size=50, required=True)
    aes_key = fields.Char(string='数据加密密钥', default=_get_default_aes_key, size=50, required=True)
    url = fields.Char(string='回调URL', size=200, default=_get_default_localhost, required=True)
    state = fields.Selection(string=u'状态', selection=[('00', '未注册'), ('01', '已注册')], default='00', copy=False)
    call_ids = fields.Many2many('dingtalk.callback.list', string=u'回调类型列表', copy=False, required=True)
    
    _sql_constraints = [
        ('value_type_uniq', 'unique(value_type)', u'事件类型重复!'),
    ]

    @api.onchange('value_type')
    def onchange_value_type(self):
        if self.value_type:
            call_ids = list()
            if self.value_type == 'all':
                for li in self.env['dingtalk.callback.list'].sudo().search([]):
                    call_ids.append(li.id)
            else:
                for li in self.env['dingtalk.callback.list'].sudo().search([('value_type', '=', self.value_type)]):
                    call_ids.append(li.id)
            self.call_ids = [(6, 0, call_ids)]

    def register_call_back(self):
        """
        注册事件
        :return:
        """
        self.ensure_one()
        # 事件类型
        call_list = list()
        for call in self.call_ids:
            call_list.append(call.value)
        try:
            result = dingtalk_api.get_client().callback.register_call_back(call_list, self.token, self.aes_key, self.url)
        except Exception as e:
            raise UserError("注册失败！原因:{}".format(e))
        if result.get('errcode') == 0:
            self.write({'state': '01'})
            self.message_post(body=u"注册回调成功")
        else:
            raise UserError("注册回调失败！原因:{}".format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}

    def update_call_back(self):
        """
        更新事件
        :return:
        """
        self.ensure_one()
        call_list = list()
        for call in self.call_ids:
            call_list.append(call.value)
        try:
            result = dingtalk_api.get_client().callback.update_call_back(call_list, self.token, self.aes_key, self.url)
        except Exception as e:
            raise UserError("更新失败！原因:{}".format(e))
        if result.get('errcode') == 0:
            self.write({'state': '01'})
            self.message_post(body=u"更新回调事件成功")
        else:
            raise UserError("更新失败！原因:{}".format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}

    def unlink(self):
        """
        重写删除方法
        :return:
        """
        for res in self:
            if res.state == '01':
                _logger.info(">>>删除事件...")
                try:
                    result = dingtalk_api.get_client().callback.delete_call_back()
                    _logger.info("删除回调事件：{}".format(result))
                except Exception as e:
                    _logger.info(e)
        super(DingTalkCallback, self).unlink()

