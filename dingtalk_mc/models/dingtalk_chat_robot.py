# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools.dingtalk_robot_api import ActionCard, DingtalkChatbot

_logger = logging.getLogger(__name__)

MESSAGETYPE = [
    ('text', '文本消息'),
    ('link', '链接消息'),
    ('markdown', 'Markdown'),
    ('action_card', '卡片消息'),
    ('image', '图片消息'),
    ('feed_card', 'feed_card'),
]


class DingTalkRobot(models.Model):
    _name = 'dingtalk.chat.robot'
    _description = "群机器人"
    _rec_name = 'name'

    active = fields.Boolean(string='有效', default=True)
    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.company)
    name = fields.Char(string='机器人名称', required=True, index=True)
    webhook = fields.Char(string='Hook地址', required=True)
    remarks = fields.Text(string='说明备注')
    chat_id = fields.Many2one(comodel_name='dingtalk.mc.chat', string='钉钉群会话', index=True, domain="[('state', '!=', 'close')]")

    def test_robot_connection(self):
        for res in self:
            logging.info(">>>机器人测试连接")
            headers = {'Content-Type': 'application/json'}
            content = "编程时要保持这种心态：就好像将来要维护你这些代码的人是一位残暴的精神病患者，而且他知道你住在哪。（Martin Golding）"
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "at": {
                    "isAtAll": True
                }
            }
            requests.post(url=res.webhook, headers=headers, data=json.dumps(data), timeout=1)
            # 创建消息日志
            self.env['dingtalk.message.log'].create({
                'company_id': self.env.user.company_id.id,
                'name': "机器人测试连接",
                'msg_type': "msg",
                'body': content,
                'result': '',
            })
            logging.info(">>>机器人测试连接End")

    @api.model
    def send_robot_message(self, robots, msg):
        """
        发送消息到指定的群机器人
        :param robots: 群机器人列表对象
        :param msg: 消息内容
        :return:
        """
        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": "ERP备注消息",
                "text": msg,
            },
        }
        for robot in robots:
            try:
                requests.post(url=robot.webhook, headers=headers, data=json.dumps(data), timeout=1)
            except Exception as e:
                logging.info(">>>发送消息到指定的群机器人失败： {}".format(str(e)))
        return True


class DingTalkRobotSendMessage(models.TransientModel):
    _name = 'dingtalk.robot.send.message'
    _description = "通过群机器人发送消息"

    msg_type = fields.Selection(string='消息类型', selection=MESSAGETYPE, default='text', required=True)
    robot_id = fields.Many2one('dingtalk.chat.robot', required=True, string='群机器人')
    chat_id = fields.Many2one('dingtalk.mc.chat', related='robot_id.chat_id', string='关联群组')
    at_user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingtalk_robot_and_hr_employee_rel',
                                   column1='message_id', column2='emp_id', string='提醒人员')
    isAtAll = fields.Boolean(string='@所有人时', default=False)
    text_message = fields.Text(string='文本消息内容')
    msg_title = fields.Char(string='消息标题', help="文本格式")
    card_message = fields.Text(string='卡片消息内容', help="支持markdown语法")
    btns = fields.One2many(comodel_name='dingtalk.robot.send.card.message.list', inverse_name='message_id',
                           string='按钮列表')
    markdown_message = fields.Text(string='Markdown消息内容', help="支持markdown语法")
    link_url = fields.Char(string='链接URL', help="点击消息时链接URL")
    link_image_url = fields.Char(string='链接图片URL', help="链接图片URL")
    link_message = fields.Text(string='消息描述', help="支持markdown语法")

    @api.onchange('chat_id')
    def _onchange_chat_id(self):
        """提醒人员下拉列表只显示群内成员
        """
        if self.chat_id:
            domain = [('id', 'in', self.chat_id.useridlist.ids)]
            return {
                'domain': {'at_user_ids': domain}
            }

    def dingtalk_robot_send_message(self):
        """
        点击通过群机器人发送消息按钮
        :return:
        """
        webhook = self.robot_id.webhook
        try:
            xiaoding = DingtalkChatbot(webhook)
            message = ""
            # 获取提醒人手机号列表
            if self.at_user_ids:
                at_mobiles = self.at_user_ids.mapped('mobile_phone')
            else:
                at_mobiles = None
            if self.msg_type == 'action_card':
                """卡片类型"""
                if len(self.btns) == 1:
                    btns = self.btns
                else:
                    btn_json_list = list()
                    for val in self.btns:
                        btn_json_list.append({'title': val.title, 'url': val.actionURL})
                    btns = btn_json_list
                btn_orientation = "1" if len(self.btns) == 2 else "0"
                actioncard = ActionCard(title=self.msg_title, text=self.card_message, btns=btns, btn_orientation=btn_orientation, hide_avatar=1)
                xiaoding.send_action_card(actioncard)
                message = self.card_message
            elif self.msg_type == 'text':
                """文本类型消息"""
                xiaoding.send_text(msg=self.text_message, is_at_all=self.isAtAll, at_mobiles=at_mobiles, at_dingtalk_ids=None)
                message = self.text_message
            elif self.msg_type == 'markdown':
                """markdown类型的消息"""
                xiaoding.send_markdown(title=self.msg_title, text=self.markdown_message, is_at_all=self.isAtAll, at_mobiles=at_mobiles, at_dingtalk_ids=[])
                message = self.markdown_message
            elif self.msg_type == 'link':
                """链接消息"""
                xiaoding.send_link(title=self.msg_title, text=self.link_message, message_url=self.link_url, pic_url=self.link_image_url)
                message = self.msg_title
            elif self.msg_type == 'image':
                """image消息"""
                xiaoding.send_image(pic_url=self.link_image_url)
                message = self.link_image_url
            elif self.msg_type == 'feed_card':
                """feed_card消息"""
                link_list = list()
                for val in self.btns:
                    link_list.append({'title': val.title, 'url': val.actionURL, 'pic_url': val.pic_url})
                xiaoding.send_feed_card(link_list)
                message = 'feed_card消息'
                # 创建消息日志
            self.env['dingtalk.message.log'].create({
                'company_id': self.env.user.company_id.id,
                'name': "群机器人发送消息",
                'msg_type': "msg",
                'body': message,
                'result': '',
            })
        except Exception:
            raise UserError(_('Webhook地址有误！'))


class CardMessageList(models.TransientModel):
    _name = 'dingtalk.robot.send.card.message.list'
    _description = '卡片消息列表'
    _rec_name = 'title'

    title = fields.Char(string='标题', required=True)
    actionURL = fields.Char(string='标题链接地址', required=True)
    pic_url = fields.Char(string='图片链接地址')
    message_id = fields.Many2one(comodel_name='dingtalk.robot.send.message', string='消息', ondelete='cascade')
