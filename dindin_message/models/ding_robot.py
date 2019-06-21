# -*- coding: utf-8 -*-
import json
import time
import logging
import requests
from requests import ReadTimeout
from odoo.exceptions import UserError
from odoo import api, fields, models
from .ding_robot_api import DingtalkChatbot, ActionCard, FeedLink, CardItem
_logger = logging.getLogger(__name__)

MESSAGETYPE = [
    ('text', '文本消息'),
    ('link', '链接消息'),
    ('markdown', 'Markdown'),
    ('action_card', '卡片消息'),
    ('image', '图片消息'),
    ('feed_card', 'feed_card'),
]

class DingDingRobot(models.Model):
    _name = 'dingding.robot'
    _description = "群机器人"
    _rec_name = 'name'

    active = fields.Boolean(string=u'active', default=True)
    name = fields.Char(string='机器人名称', required=True, index=True)
    webhook = fields.Char(string='Hook地址', required=True)
    remarks = fields.Text(string=u'说明备注')
    chat_id = fields.Many2one(comodel_name='dingding.chat', string=u'关联群组', index=True)

    @api.multi
    def test_robot_connection(self):
        for res in self:
            logging.info(">>>机器人测试连接")
            headers = {'Content-Type': 'application/json'}
            data = {
                "msgtype": "text",
                "text": {
                    "content": "编程时要保持这种心态：就好像将来要维护你这些代码的人是一位残暴的精神病患者，而且他知道你住在哪。（Martin Golding）"
                },
                "at": {
                    "isAtAll": True
                }
            }
            requests.post(url=res.webhook, headers=headers, data=json.dumps(data), timeout=1)
            logging.info(">>>机器人测试连接End")

            webhook = res.webhook
            # 用户手机号列表
            at_mobiles = ['*************************这里填写需要提醒的用户的手机号码，字符串或数字都可以****************************']
            # 初始化机器人小丁
            xiaoding = DingtalkChatbot(webhook)
            # text
            xiaoding.send_text(msg='我就是小丁，小丁就是我！', is_at_all=True)
            xiaoding.send_text(msg='我就是小丁，小丁就是我！', at_mobiles='')

            # image表情
            xiaoding.send_image(pic_url='http://uc-test-manage-00.umlife.net/jenkins/pic/flake8.png')

            # link
            xiaoding.send_link(title='万万没想到，某小璐竟然...', text='故事是这样子的...', message_url='http://www.kwongwah.com.my/?p=454748", pic_url="https://pbs.twimg.com/media/CEwj7EDWgAE5eIF.jpg')

            # markdown
            # 1、提醒所有人
            xiaoding.send_markdown(title='氧气文字', text='#### 广州天气\n'
                                '> 9度，西北风1级，空气良89，相对温度73%\n\n'
                                '> ![美景](http://www.sinaimg.cn/dy/slidenews/5_img/2013_28/453_28488_469248.jpg)\n'
                                '> ###### 10点20分发布 [天气](http://www.thinkpage.cn/) \n',
                                is_at_all=True)
            # 2、提醒指定手机用户，需要在text参数中@用户
            xiaoding.send_markdown(title='氧气文字', text='#### 广州天气\n'
                                '> 9度，西北风1级，空气良89，相对温度73%\n\n'
                                '> ![美景](http://www.sinaimg.cn/dy/slidenews/5_img/2013_28/453_28488_469248.jpg)\n'
                                '> ###### 10点20分发布 [天气](http://www.thinkpage.cn/) \n',
                                at_mobiles='')

            # 整体跳转ActionCard
            btns1 = [CardItem(title="查看详情", url="https://www.dingtalk.com/")]
            actioncard1 = ActionCard(title='万万没想到，竟然...',
                                    text='![markdown](http://www.songshan.es/wp-content/uploads/2016/01/Yin-Yang.png) \n### 故事是这样子的...',
                                    btns=btns1,
                                    btn_orientation=1,
                                    hide_avatar=1)
            xiaoding.send_action_card(actioncard1)

            # 单独跳转ActionCard
            # 1、两个按钮选择
            btns2 = [CardItem(title="支持", url="https://www.dingtalk.com/"), CardItem(title="反对", url="https://www.dingtalk.com/")]
            actioncard2 = ActionCard(title='万万没想到，竟然...',
                                    text='![markdown](http://www.songshan.es/wp-content/uploads/2016/01/Yin-Yang.png) \n### 故事是这样子的...',
                                    btns=btns2,
                                    btn_orientation=1,
                                    hide_avatar=1)
            xiaoding.send_action_card(actioncard2)
            # 2、三个按钮选择
            btns3 = [CardItem(title="支持", url="https://www.dingtalk.com/"), CardItem(title="中立", url="https://www.dingtalk.com/"), CardItem(title="反对", url="https://www.dingtalk.com/")]
            actioncard3 = ActionCard(title='万万没想到，竟然...',
                                    text='![markdown](http://www.songshan.es/wp-content/uploads/2016/01/Yin-Yang.png) \n### 故事是这样子的...',
                                    btns=btns3,
                                    btn_orientation=1,
                                    hide_avatar=1)
            xiaoding.send_action_card(actioncard3)

            # FeedCard类型
            card1 = CardItem(title="氧气美女", url="https://www.dingtalk.com/", pic_url="https://unzippedtv.com/wp-content/uploads/sites/28/2016/02/asian.jpg")
            card2 = CardItem(title="氧眼美女", url="https://www.dingtalk.com/", pic_url="https://unzippedtv.com/wp-content/uploads/sites/28/2016/02/asian.jpg")
            card3 = CardItem(title="氧神美女", url="https://www.dingtalk.com/", pic_url="https://unzippedtv.com/wp-content/uploads/sites/28/2016/02/asian.jpg")
            cards = [card1, card2, card3]
            xiaoding.send_feed_card(cards)


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
            # "at": {
            #     "atMobiles": [
            #         "156xxxx8827",
            #         "189xxxx8325"
            #     ],
            #     "isAtAll": False
            # }
        }
        for robot in robots:
            try:
                requests.post(url=robot.webhook, headers=headers, data=json.dumps(data), timeout=1)
            except Exception:
                logging.info(">>>发送消息到指定的群机器人失败")
        return True

class DingDingRobotSendMessage(models.TransientModel):
    _name = 'dingding.robot.send.message'
    _description = "通过群机器人发送消息"

    msg_type = fields.Selection(string=u'消息类型', selection=MESSAGETYPE, default='text', required=True)
    robot_id = fields.Many2one('dingding.robot', required=True, string='群机器人')
    chat_id = fields.Many2one('dingding.chat', related='robot_id.chat_id', string='关联群组')
    at_user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_robot_and_hr_employee_rel',
                                  column1='message_id', column2='emp_id', string=u'提醒人员')                  
    isAtAll = fields.Boolean(string='@所有人时', default=False)
    text_message = fields.Text(string='文本消息内容')
    msg_title = fields.Char(string='消息标题', help="文本格式")
    card_message = fields.Text(string='卡片消息内容', help="支持markdown语法")
    btns = fields.One2many(comodel_name='dingding.robot.send.card.message.list', inverse_name='message_id',
                                       string=u'按钮列表')
    markdown_message = fields.Text(string='Markdown消息内容', help="支持markdown语法")
    link_url = fields.Char(string='链接URL', help="点击消息时链接URL")
    link_image_url = fields.Char(string='链接图片URL', help="链接图片URL")
    link_message = fields.Text(string='消息描述', help="支持markdown语法")


    @api.onchange('chat_id')
    def _onchange_chat_id(self):
        """提醒人员下拉列表只显示群内成员
        """
        if self.chat_id:
            domain = [('id','in', self.chat_id.useridlist.ids)]
            return {
            'domain': {'at_user_ids': domain}
            }

    @api.multi
    def dingding_robot_send_message(self):
        """
        点击通过群机器人发送消息按钮
        :return:
        """
        webhook = self.robot_id.webhook
        xiaoding = DingtalkChatbot(webhook)
        # 获取提醒人手机号列表
        if self.at_user_ids:
            at_mobiles = self.at_user_ids.mapped('mobile_phone')
        if self.msg_type == 'action_card':
            """卡片类型"""
            if len(self.btns) == 1:
                btns= self.btns
            else:
                btn_json_list = list()
                for val in self.btns:
                    btn_json_list.append({'title': val.title, 'url': val.actionURL})
                btns= btn_json_list
            btn_orientation = "1" if len(self.btns) == 2 else "0"
            actioncard = ActionCard(title=self.msg_title,
                                    text=self.card_message,
                                    btns=btns,
                                    btn_orientation=btn_orientation,
                                    hide_avatar=1)
            xiaoding.send_action_card(actioncard) 
        elif self.msg_type == 'text':
            """文本类型消息"""
            xiaoding.send_text(msg=self.text_message, is_at_all=self.isAtAll, at_mobiles=at_mobiles, at_dingtalk_ids=None)
        elif self.msg_type == 'markdown':
            """markdown类型的消息"""
            xiaoding.send_markdown(title=self.msg_title, text=self.markdown_message, is_at_all=self.isAtAll, at_mobiles=at_mobiles, at_dingtalk_ids=[])
        elif self.msg_type == 'link':
            """链接消息"""
            xiaoding.send_link(title=self.msg_title, text=self.link_message, message_url=self.link_url, pic_url=self.link_image_url)
        elif self.msg_type == 'image':
            """image消息"""
            xiaoding.send_image(pic_url=self.link_image_url)
        elif self.msg_type == 'feed_card':
            """feed_card消息"""

            link_list = list()
            for val in self.btns:
                link_list.append({'title': val.title, 'url': val.actionURL, 'pic_url': val.pic_url})
            xiaoding.send_feed_card(link_list)

class CardMessageList(models.TransientModel):
    _name = 'dingding.robot.send.card.message.list'
    _description = '卡片消息列表'
    _rec_name = 'title'

    title = fields.Char(string='标题', required=True)
    actionURL = fields.Char(string='标题链接地址', required=True)
    pic_url = fields.Char(string='图片链接地址')
    message_id = fields.Many2one(comodel_name='dingding.robot.send.message', string=u'消息', ondelete='cascade')

class DinDinWorkMessageUserList(models.TransientModel):
    _name = 'dingding.robot.send.user.list'
    _rec_name = 'emp_id'
    _description = "@提醒人列表"

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    mobile_phone = fields.Char(string='电话')
    job_title = fields.Char(string='职位')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', ondelete='cascade')
    message_id = fields.Many2one(comodel_name='dingding.robot.send.message', string=u'消息', ondelete='cascade')

    @api.onchange('emp_id')
    def onchange_emp(self):
        if self.emp_id:
            self.mobile_phone = self.emp_id.mobile_phone
            self.job_title = self.emp_id.job_title
            self.department_id = self.emp_id.department_id.id