# -*- coding: utf-8 -*-
import json
import logging
import random
import string
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class DingDingCallback(models.Model):
    _name = 'dingding.callback.manage'
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
        return "{}dingding/callback/eventreceive".format(request.httprequest.host_url)

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
    call_ids = fields.Many2many('dingding.callback.list', string=u'回调类型列表', copy=False, required=True)
    
    _sql_constraints = [
        ('value_type_uniq', 'unique(value_type)', u'事件类型重复!'),
    ]

    @api.onchange('value_type')
    def onchange_value_type(self):
        if self.value_type:
            call_ids = list()
            if self.value_type == 'all':
                for li in self.env['dingding.callback.list'].sudo().search([]):
                    call_ids.append(li.id)
            else:
                for li in self.env['dingding.callback.list'].sudo().search([('value_type', '=', self.value_type)]):
                    call_ids.append(li.id)
            self.call_ids = [(6, 0, call_ids)]

    @api.multi
    def register_call_back(self):
        """
        注册事件
        :return:
        """
        logging.info(">>>注册事件...")
        for res in self:
            url, token = self.env['dingding.parameter'].get_parameter_value_and_token('register_call_back')
            call_list = list()
            for call in res.call_ids:
                call_list.append(call.value)
            data = {
                'call_back_tag': call_list,
                'token': res.token,
                'aes_key': res.aes_key,
                'url': res.url,
            }
            result = self.env['dingding.api.tools'].send_post_request(url, token, data, 2)
            if result.get('errcode') == 0:
                self.write({'state': '01'})
                self.message_post(body=u"注册事件成功")
            else:
                raise UserError("注册失败！原因:{}".format(result.get('errmsg')))
        logging.info(">>>注册事件End...")

    @api.multi
    def update_call_back(self):
        """
        更新事件
        :return:
        """
        for res in self:
            url, token = self.env['dingding.parameter'].get_parameter_value_and_token('update_call_back')
            call_list = list()
            for call in res.call_ids:
                call_list.append(call.value)
            data = {
                'call_back_tag': call_list,
                'token': res.token,
                'aes_key': res.aes_key,
                'url': res.url,
            }
            result = self.env['dingding.api.tools'].send_post_request(url, token, data, 2)
            if result.get('errcode') == 0:
                self.write({'state': '01'})
                self.message_post(body=u"更新事件成功")
            else:
                raise UserError("更新失败！原因:{}".format(result.get('errmsg')))

    @api.multi
    def unlink(self):
        """
        重写删除方法
        :return:
        """
        for res in self:
            if res.state == '01':
                self.delete_call_back(res.token)
        super(DingDingCallback, self).unlink()

    @api.model
    def delete_call_back(self, call_token):
        logging.info(">>>删除事件...")
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('delete_call_back')
        data = {
            'access_token': call_token,
        }
        result = self.env['dingding.api.tools'].send_get_request(url, token, data, 1)
        logging.info(result)
        if result.get('errcode') == 0:
            logging.info("已删除token为{}的回调事件".format(call_token))
        else:
            raise UserError("删除钉钉后台的回调失败！请稍后再试！")
        logging.info(">>>删除事件End...")

    @api.model
    def get_all_call_back(self):
        """
        获取所有回调列表
        :return:
        """
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('get_call_back')
        try:
            result = requests.get(url="{}{}".format(url, token), timeout=3)
            result = json.loads(result.text)
            logging.info("获取所有回调列表结果:{}".format(result))
            if result.get('errcode') != 0:
                return {'state': False, 'msg': result.get('errmsg')}
            else:
                tag_list = list()
                for tag in result.get('call_back_tag'):
                    callback_list = self.env['dingding.callback.list'].search([('value', '=', tag)])
                    if callback_list:
                        tag_list.append(callback_list[0].id)
                callback = self.env['dingding.callback.manage'].search([('url', '=', result.get('url'))])
                data = {
                    'call_ids': [(6, 0, tag_list)],
                    'url': result.get('url'),
                    'aes_key': result.get('aes_key'),
                    'token': result.get('token'),
                    'state': '01',
                }
                if callback:
                    callback.write(data)
                else:
                    self.env['dingding.callback.manage'].create(data)
                return {'state': True}
        except ReadTimeout:
            return {'state': False, 'msg': '网络连接超时'}
