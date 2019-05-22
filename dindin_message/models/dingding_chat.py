# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingChat(models.Model):
    _name = 'dingding.chat'
    _description = "钉钉群会话"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    chat_id = fields.Char(string='群会话Id')
    name = fields.Char(string='群名称', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'群主', required=True)
    show_history_type = fields.Selection(string=u'聊天历史消息', selection=[(0, '否'), (1, '是'), ], default=0,
                                         help="新成员是否可查看聊天历史消息,新成员入群是否可查看最近100条聊天记录")
    searchable = fields.Selection(string=u'群可搜索', selection=[(0, '否'), (1, '是'), ], default=0)
    validation_type = fields.Selection(string=u'入群验证', selection=[(0, '否'), (1, '是'), ], default=0)
    mention_all_authority = fields.Selection(string=u'@all 权限', selection=[(0, '所有人'), (1, '仅群主'), ], default=0)
    chat_banned_type = fields.Selection(string=u'群禁言', selection=[(0, '不禁言'), (1, '全员禁言'), ], default=0)
    management_ype = fields.Selection(string=u'管理类型', selection=[(0, '所有人可管理'), (1, '仅群主可管理'), ], default=1)
    useridlist = fields.Many2many(comodel_name='hr.employee', relation='dingding_chat_and_hr_employee_rel',
                                  column1='chat_id', column2='emp_id', string=u'群成员', required=True)
    state = fields.Selection(string=u'状态', selection=[('new', '新建'), ('normal', '已建立'), ('close', '解散'), ],
                             default='new', track_visibility='onchange')

    @api.multi
    def create_dingding_chat(self):
        """
        创建群会话
        :return:
        """
        for res in self:
            self.check_employee_din_id(res)
            logging.info(">>>开始钉钉创建群会话")
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_create')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'name': res.name,
                'owner': res.employee_id.din_id,
                'showHistoryType': res.show_history_type,
                'searchable': res.searchable,
                'validationType': res.validation_type,
                'mentionAllAuthority': res.mention_all_authority,
                'chatBannedType': res.chat_banned_type,
                'managementType': res.management_ype,
                'useridlist': user_list,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    res.write({'chat_id': result.get('chatid'), 'state': 'normal'})
                    res.message_post(body=u"群会话已创建!群会话的ID:{}".format(result.get('chatid')), message_type='notification')
                else:
                    raise UserError('创建失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")

    @api.multi
    def write_dingding_chat(self):
        """
        修改群会话
        :return:
        """
        for res in self:
            self.check_employee_din_id(res)
            logging.info(">>>开始钉钉修改群会话")
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'chat_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'chatid': res.chat_id,
                'name': res.name,
                'owner': res.employee_id.din_id,
                'showHistoryType': res.show_history_type,
                'searchable': res.searchable,
                'validationType': res.validation_type,
                'mentionAllAuthority': res.mention_all_authority,
                'chatBannedType': res.chat_banned_type,
                'managementType': res.management_ype,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                logging.info(">>>返回结果{}".format(result))
                if result.get('errcode') == 0:
                    res.message_post(body=u"群会话已修改!", message_type='notification')
                else:
                    raise UserError('修改失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")

    @api.model
    def check_employee_din_id(self, res):
        if not res.employee_id.din_id:
            raise UserError("员工（群主）在钉钉中不存在，请选择其他人员!")
        user_list = list()
        for emp in res.useridlist:
            if not emp.din_id:
                raise UserError("员工{}:在钉钉中不存在，请选择其他人员!".format(emp.name))
            user_list.append(emp.din_id)


class DingDingChatUserModel(models.TransientModel):
    _name = 'dingding.chat.user.model'
    _description = "群会话用户模型"

    user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_chat_user_model_and_hr_employee_rel',
                                column1='model_id', column2='emp_id', string=u'群成员', required=True)


class DingDingChatList(models.TransientModel):
    _name = 'get.dingding.chat.list'
    _description = "获取群已存在的会话"

    @api.multi
    def get_chat_list(self):
        """
        获取群会话
        :return:
        """
        for res in self:
            logging.info(">>>开始获取群会话...")
