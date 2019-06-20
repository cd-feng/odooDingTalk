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
            # headers = {'Content-Type': 'application/json'}
            # data = {
            #     "msgtype": "text",
            #     "text": {
            #         "content": "编程时要保持这种心态：就好像将来要维护你这些代码的人是一位残暴的精神病患者，而且他知道你住在哪。（Martin Golding）"
            #     },
            #     "at": {
            #         "isAtAll": True
            #     }
            # }
            # requests.post(url=res.webhook, headers=headers, data=json.dumps(data), timeout=1)
            # logging.info(">>>机器人测试连接End")

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

    message = fields.Text(string=u'消息内容', required=True)
    message_id = fields.Many2one(comodel_name='dindin.work.message', string=u'消息', ondelete='cascade')
    robot_id = fields.Many2one('dingding.robot', required=True, string='群机器人')
    chat_id = fields.Many2one('dingding.chat', related='robot_id.chat_id', string='关联群组')
    at_mobiles = fields.Char("@提醒人")
    isAtAll = fields.Boolean(string='@所有人时', default=False)

    @api.multi
    def dingding_robot_send_message(self):
        """
        点击通过群机器人发送消息按钮
        :return:
        """

        webhook = self.robot_id.webhook
        data =  {
                    "msgtype": "text", 
                    "text": {
                        "content": self.message
                    }, 
                    "at": {
                        "atMobiles": self.at_mobiles,
                        "isAtAll": self.isAtAll
                    }
                }

        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url= webhook, headers=headers, data=json.dumps(data), timeout=5)
        except ReadTimeout:
            raise UserError("网络连接超时！")
