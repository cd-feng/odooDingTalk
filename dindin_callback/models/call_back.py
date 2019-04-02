# -*- coding: utf-8 -*-
import json
import logging
import random
import string

import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinCallback(models.Model):
    _name = 'dindin.users.callback'
    _inherit = ['mail.thread']
    _description = "钉钉回调管理"
    _rec_name = 'call_id'

    @api.model
    def _get_default_aes_key(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 43))

    @api.model
    def _get_default_token(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 10))

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    call_id = fields.Many2one(comodel_name='dindin.users.callback.list', string=u'回调类型', ondelete='cascade')
    token = fields.Char(string='Token', default=_get_default_token, size=50)
    aes_key = fields.Char(string='数据加密密钥', default=_get_default_aes_key, size=50)
    url = fields.Char(string='回调URL', size=200)
    state = fields.Selection(string=u'状态', selection=[('00', '未注册'), ('01', '已注册')], default='00')

    _sql_constraints = [
        ('vcall_id_uniq', 'unique(call_id)', u'回调类型重复!'),
    ]

    @api.onchange('call_id')
    def onchage_call_type(self):
        if self.call_id:
            self.url = self.call_id.call_back_url

    @api.multi
    def register_call_back(self):
        """
        注册事件
        :return:
        """
        logging.info(">>>注册事件...")
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'register_call_back')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            call_list = list()
            call_list.append(res.call_id.value)
            data = {
                'call_back_tag': call_list if call_list else '',
                'token': res.token if res.token else '',
                'aes_key': res.aes_key if res.aes_key else '',
                'url': res.url if res.url else '',
            }
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    self.write({'state': '01'})
                    self.message_post(body=u"注册事件成功")
                else:
                    raise UserError("注册失败！原因:{}".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        logging.info(">>>注册事件End...")

    @api.multi
    def update_call_back(self):
        """
        更新事件
        :return:
        """
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'update_call_back')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            call_list = list()
            call_list.append(res.call_id.value)
            data = {
                'call_back_tag': call_list if call_list else '',
                'token': res.token if res.token else '',
                'aes_key': res.aes_key if res.aes_key else '',
                'url': res.url if res.url else '',
            }
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    self.write({'state': '01'})
                    self.message_post(body=u"更新事件成功")
                else:
                    raise UserError("更新失败！原因:{}".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")

    @api.multi
    def unlink(self):
        """
        重写删除方法
        :return:
        """
        for res in self:
            if res.state == '01':
                self.delete_call_back(res.token)
        super(DinDinCallback, self).unlink()

    @api.model
    def delete_call_back(self, call_token):
        logging.info(">>>删除事件...")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'delete_call_back')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'access_token': call_token,
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=5)
            result = json.loads(result.text)
            logging.info(result)
            if result.get('errcode') == 0:
                logging.info("已删除token为{}的回调事件".format(token))
            else:
                raise UserError("删除事件失败！原因:{}".format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时")
        logging.info(">>>删除事件End...")

    # TODO 未完善
    @api.model
    def get_all_call_back(self):
        """
        获取所有回调列表
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'get_call_back')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        try:
            result = requests.get(url="{}{}".format(url, token), timeout=5)
            result = json.loads(result.text)
            logging.info("获取所有回调列表结果:{}".format(result))
            if result.get('errcode') != 0:
                return {'state': False, 'msg': result.get('errmsg')}
            else:
                print(result)
                return {'state': True}
        except ReadTimeout:
            return {'state': False, 'msg': '网络连接超时'}
