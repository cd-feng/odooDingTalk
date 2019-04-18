# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinCalendarEvent(models.Model):
    _inherit = 'calendar.event'

    number = fields.Char(string='日程编号', copy=False)
    d_minutes = fields.Integer(string=u'前?分钟提醒')
    dingtalk_calendar_id = fields.Char(string='钉钉日历id')

    @api.model
    def create(self, values):
        if not values['number']:
            values['number'] = self.env['ir.sequence'].sudo().next_by_code('calendar.event.number')
        auto_calendar_event = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.auto_calendar_event')
        if auto_calendar_event:
            values['dingtalk_calendar_id'] = self.create_dindin_calendar(values)
            self.sudo().message_post(body=u"已同步上传至钉钉日程", message_type='notification')
        return super(DinDinCalendarEvent, self).create(values)

    @api.model
    def create_dindin_calendar(self, val):
        """
        创建钉钉日程
        :param val:
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'calendar_create')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        start_time = datetime.datetime.strptime("{}.42".format(val.get('start')), "%Y-%m-%d %H:%M:%S.%f").timetuple()
        end_time = datetime.datetime.strptime("{}.42".format(str(val.get('stop'))), "%Y-%m-%d %H:%M:%S.%f").timetuple()
        user = self.env['res.users'].sudo().search([('id', '=', val.get('user_id'))])
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        userids = list()
        userids.append(employee.din_id)
        data = {
            'create_vo': {
                'summary': val.get('name'),  # 主题
                'minutes': val.get('d_minutes'),  # 前分钟提醒
                'remind_type': 'app',  # 提醒方式-固定值
                'location': val.get('location') if val.get('location') else '',  # 地点地址
                'receiver_userids': userids,  # 接收人列表string
                'end_time': {
                    'unix_timestamp': "{}000".format(int(time.mktime(end_time))),  # 结束的unix时间戳 (单位:毫秒)
                    'timezone': 'Shanghai',   # 时区
                },
                'calendar_type': 'notification',  # 提醒类型
                'start_time': {
                    'unix_timestamp': "{}000".format(int(time.mktime(start_time))),  # 开始的unix时间戳
                    'timezone': 'Shanghai',  # 时区
                },
                'source': {
                    'title': 'OdooERP',
                    'url': 'http://#',
                },
                'description': val.get('description') if val.get('description') else ' ',  # 备注
                'creator_userid': employee[0].din_id if employee[0].din_id else '',  # 创建人uid
                'uuid': val.get('number'),  # 流水号
                'biz_id': val.get('number'),  # 业务号
            }
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            logging.info(">>>创建日程返回结果:{}".format(result))
            if result.get('errcode') == 0:
                res = result.get('result')
                return res.get('dingtalk_calendar_id')
            else:
                raise UserError("上传钉钉日程失败,原因:{}".format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传钉钉日程网络连接超时,请重试!")
