# -*- coding: utf-8 -*-
import logging
import random
import string
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingTalkCallback(models.Model):
    _name = 'dingtalk.callback.manage'
    _inherit = ['mail.thread']
    _description = "回调列表"
    _rec_name = 'company_id'

    @api.model
    def _get_default_aes_key(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 43))

    @api.model
    def _get_default_token(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 10))

    @api.model
    def _get_default_localhost(self):
        return "{}web/dingtalk/callback/action".format(request.httprequest.host_url)

    ValueType = [
        ('all', '所有事件'),
        ('00', '通讯录事件'),
        ('01', '群会话事件'),
        ('02', '签到事件'),
        ('03', '审批事件'),
        ('04', '考勤事件'),
    ]

    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.company)
    value_type = fields.Selection(string=u'事件类型', selection=ValueType, default='all', copy=False, required=True)
    token = fields.Char(string='Token', default=_get_default_token, size=50, required=True)
    aes_key = fields.Char(string='加密密钥', default=_get_default_aes_key, size=50, required=True)
    url = fields.Char(string='回调URL', size=200, default=_get_default_localhost, required=True)
    state = fields.Selection(string=u'状态', selection=[('00', '未注册'), ('01', '已注册')], default='00', copy=False)
    call_ids = fields.Many2many('dingtalk.callback.list', string=u'回调类型列表', copy=False, required=True)

    _sql_constraints = [
        ('value_type_uniq', 'unique(company_id)', u'该公司已经有一个回调事件了!'),
    ]

    @api.onchange('value_type')
    def onchange_value_type(self):
        if self.value_type:
            call_ids = list()
            if self.value_type == 'all':
                for li in self.env['dingtalk.callback.list'].with_user(SUPERUSER_ID).search([]):
                    call_ids.append(li.id)
            else:
                for li in self.env['dingtalk.callback.list'].with_user(SUPERUSER_ID).search([('value_type', '=', self.value_type)]):
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
            client = dt.get_client(self, dt.get_dingtalk_config(self, self.company_id))
            result = client.post('call_back/register_call_back', {
                'call_back_tag': call_list,
                'aes_key': self.aes_key,
                'token': self.token,
                'url': self.url,
            })
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
            client = dt.get_client(self, dt.get_dingtalk_config(self, self.company_id))
            result = client.post('call_back/update_call_back', {
                'call_back_tag': call_list,
                'aes_key': self.aes_key,
                'token': self.token,
                'url': self.url,
            })
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
                    client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
                    result = client.callback.delete_call_back()
                    _logger.info("删除回调事件：{}".format(result))
                except Exception as e:
                    _logger.info(e)
        return super(DingTalkCallback, self).unlink()
