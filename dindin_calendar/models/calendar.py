# -*- coding: utf-8 -*-
import datetime
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinCalendarEvent(models.Model):
    _inherit = 'calendar.event'

    number = fields.Char(string='日程编号', copy=False)
    d_minutes = fields.Integer(string=u'前?分钟提醒')

    @api.model
    def create(self, values):
        if not values['number']:
            values['number'] = self.env['ir.sequence'].sudo().next_by_code('calendar.event.number')
        self.create_dindin_calendar(values)
        return super(DinDinCalendarEvent, self).create(values)

    # TODO 由于钉钉接口有误，待完成开发
    @api.model
    def create_dindin_calendar(self, val):
        """
        创建钉钉日程
        :param val:
        :return:
        """
        print(val)
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'calendar_create')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        start_time = datetime.datetime.strptime("{}.42".format(str(val.get('start_datetime'))),
                                                "%Y-%m-%d %H:%M:%S.%f").timetuple()
        end_time = datetime.datetime.strptime("{}.42".format(str(val.get('stop_datetime'))),
                                              "%Y-%m-%d %H:%M:%S.%f").timetuple()
        user = self.env['res.users'].sudo().search([('id', '=', val.get('user_id'))])
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        data = {
            'create_vo': {
                'summary': val.get('name'),  # 主题
                'minutes': val.get('d_minutes'),  # 前分钟提醒
                'remind_type': 'app',  # 提醒方式-固定值
                'location': val.get('location') if val.get('location') else '',  # 地点地址
                'receiver_userids': 'app',  # 接收人列表string
                'end_time': val.get('stop_datetime'),  # 结束时间
                'unix_timestamp': end_time,  # 结束时间毫秒
                'timezone': 'Asia/Shanghai',  # 时区
                'calendar_type': 'notification',  # 提醒类型
                'start_time': val.get('start_datetime'),  # 开始时间
                # 'unix_timestamp':  'notification',   # 开始时间毫秒
                'url': 'http://#',  # 跳转url
                'description': val.get('description') if val.get('description') else ' ',  # 备注
                'creator_userid': employee[0].din_id if employee[0].din_id else '',  # 创建人uid
                'uuid': val.get('number'),  # 流水号
                'biz_id': val.get('number'),  # 业务号
            }
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(">>>创建日程返回结果:{}".format(result))
            if result.get('errcode') == 0:
                logging.info("2122")
        except ReadTimeout:
            raise UserError("创建日程网络连接超时,请重试!")
