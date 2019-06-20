# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import api, fields, models

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
