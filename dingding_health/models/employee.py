# -*- coding: utf-8 -*-
import datetime
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    health_state = fields.Selection(string=u'运动状态', selection=[('open', '开启'), ('close', '关闭')], default='open')
    dd_step_count = fields.Integer(string=u'运动步数', compute='get_user_today_health')

    @api.multi
    def get_user_today_health(self):
        """
        获取员工在今日的步数
        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_user_health_info'):
            url = self.env['dingding.parameter'].search([('key', '=', 'get_health_list')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            for res in self:
                if res.ding_id:
                    today = datetime.date.today()
                    formatted_today = today.strftime('%Y%m%d')
                    data = {
                        'type': 0,
                        'object_id': res.ding_id,
                        'stat_dates': formatted_today,
                    }
                    headers = {'Content-Type': 'application/json'}
                    try:
                        result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=1)
                        result = json.loads(result.text)
                        logging.info(result)
                        if result.get('errcode') == 0:
                            for stepinfo_list in result.get('stepinfo_list'):
                                res.update({'dd_step_count': stepinfo_list['step_count']})
                        else:
                            res.update({'dd_step_count': 0})
                    except ReadTimeout:
                        logging.info(">>>获取运动数据超时！")
                else:
                    res.update({'dd_step_count': 0})

    @api.multi
    def get_user_health_state(self):
        """
        获取员工钉钉运动开启状态
        :return:
        """
        for res in self:
            url = self.env['dingding.parameter'].search([('key', '=', 'get_user_health_status')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            if res.ding_id:
                data = {'userid': res.ding_id}
                headers = {'Content-Type': 'application/json'}
                try:
                    result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                           timeout=1)
                    result = json.loads(result.text)
                    logging.info(result)
                    if result.get('errcode') == 0:
                        if result['status']:
                            res.update({'health_state': 'open'})
                        else:
                            res.update({'health_state': 'close'})
                except ReadTimeout:
                    logging.info(">>>获取运动状态超时！")

    @api.model
    def get_time_stamp(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000) 
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    # 把时间转成时间戳形式
    @api.model
    def date_to_stamp(self, date):
        """
        将时间转成13位时间戳
        :param time_num:
        :return:
        """
        date_str = fields.Datetime.to_string(date)
        date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
        date_stamp = date_stamp * 1000
        return date_stamp
