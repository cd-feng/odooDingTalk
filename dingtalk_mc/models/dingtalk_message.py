# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingtalkLog(models.Model):
    _description = "消息日志"
    _name = 'dingtalk.message.log'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.company)
    name = fields.Char(string="名称")
    msg_type = fields.Selection(string="消息类型", selection=[('chat', '群消息'), ('work', '工作通知'), ('msg', '普通消息')])
    body = fields.Text(string="消息内容")
    result = fields.Text(string="返回结果")


class DingTalkSendChatMessage(models.TransientModel):
    _name = 'dingtalk.send.chat.message'
    _description = "发送群消息"

    message = fields.Text(string='消息内容', required=True)

    def send_dingtalk_test_message(self):
        """
        点击群会话发送群消息按钮
        :return:
        """
        self.ensure_one()
        chat_id = self.env.context.get('active_id', False)
        ding_chat = self.env['dingtalk.mc.chat'].browse(chat_id)
        msg = {
            "msgtype": "text",
            "text": {
                "content": self.message
            }
        }
        try:
            client = dt.get_client(self, dt.get_dingtalk_config(self, ding_chat.company_id))
            result = client.chat.send(ding_chat.chat_id, msg)
            # 创建消息日志
            self.env['dingtalk.message.log'].create({
                'company_id': self.env.company.id,
                'name': "发送群消息",
                'msg_type': "chat",
                'body': self.message,
                'result': result,
            })
        except Exception as e:
            raise UserError(e)

    @api.model
    def send_message(self, ding_chat, body):
        """
        发送群会话消息
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        chatid = ding_chat.chat_id
        msg = {
            "msgtype": "markdown",
            "markdown": {
                "title": "来自ERP的备注消息",
                "text": body
            }
        }
        try:
            result = din_client.chat.send(chatid, msg)
            logging.info(">>>发送群消息返回结果%s", result)
        except Exception as e:
            raise UserError(e)
        return True

    @api.model
    def send_work_message(self, userstr, message):
        """
        发送工作消息到指定员工列表
        :param userstr 员工列表  string
        :param message 消息内容
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        # agentid = self.env['ir.config_parameter'].sudo(
        # ).get_param('ali_dingding.din_agentid')
        agentid = tools.config.get('din_agentid', '')
        userid_list = userstr
        msg_body = {
            "msgtype": "markdown",
            "markdown": {
                "title": "来自ERP的消息",
                "text": message
            }
        }
        try:
            result = din_client.message.send(
                agentid, msg_body, touser_list=userid_list, toparty_list=())
            logging.info(">>>发送待办消息返回结果%s", result)
        except Exception as e:
            raise UserError(e)
        return True
