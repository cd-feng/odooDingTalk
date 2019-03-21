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


class DinDinApprovalTemplate(models.Model):
    _name = 'dindin.approval.template'
    _description = "审批模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    process_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)

    @api.multi
    def find_department_sign(self):
        """获取部门签到记录"""
        logging.info(">>>获取部门用户签到记录...")
        for res in self:
            res.line_ids = False
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'get_dept_checkin')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            start_time = datetime.datetime.strptime("{}.42".format(str(res.start_time)),
                                                    "%Y-%m-%d %H:%M:%S.%f").timetuple()
            end_time = datetime.datetime.strptime("{}.42".format(str(res.end_time)), "%Y-%m-%d %H:%M:%S.%f").timetuple()
            data = {
                'department_id': res.department_id.din_id,
                'start_time': "{}000".format(int(time.mktime(start_time))),
                'end_time': "{}000".format(int(time.mktime(end_time))),
            }
            if res.is_root:
                data.update({'department_id': '1'})
            try:
                result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    line_list = list()
                    for data in result.get('data'):
                        emp = self.env['hr.employee'].sudo().search([('din_id', '=', data.get('userId'))])
                        timestamp = self.get_time_stamp(data.get('timestamp'))
                        line_list.append({
                            'emp_id': emp.id if emp else False,
                            'timestamp': timestamp,
                            'place': data.get('place'),
                            'detailPlace': data.get('detailPlace'),
                            'remark': data.get('remark'),
                            'latitude': data.get('latitude'),
                            'longitude': data.get('longitude'),
                            'avatar': data.get('avatar'),
                        })
                    res.line_ids = line_list
            except ReadTimeout:
                raise UserError("获取部门签到记录网络连接超时")

    @api.model
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间
        :param timeNum:
        :return:
        """
        timeStamp = float(timeNum / 1000)
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime
