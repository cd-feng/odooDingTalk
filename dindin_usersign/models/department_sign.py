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


class DinDinDepartmentSign(models.Model):
    _name = 'dindin.department.signs'
    _description = "部门签到记录"
    _rec_name = 'department_id'

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', required=True)
    is_root = fields.Boolean(string=u'根部门', default=False)
    start_time = fields.Datetime(string=u'开始时间', required=True)
    end_time = fields.Datetime(string=u'结束时间', required=True)
    line_ids = fields.One2many(comodel_name='dindin.department.signs.line', inverse_name='signs_id', string=u'列表')

    @api.multi
    def find_department_sign(self):
        """获取部门签到记录"""
        logging.info(">>>获取部门用户签到记录...")
        for res in self:
            res.line_ids = False
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'get_dept_checkin')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            start_time = datetime.datetime.strptime("{}.42".format(str(res.start_time)), "%Y-%m-%d %H:%M:%S.%f").timetuple()
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


class DinDinDepartmentSignLine(models.Model):
    _name = 'dindin.department.signs.line'
    _description = "部门签到记录列表"
    _rec_name = 'emp_id'

    signs_id = fields.Many2one(comodel_name='dindin.department.signs', string=u'签到', ondelete='cascade')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    timestamp = fields.Datetime(string=u'签到时间')
    place = fields.Char(string='签到地址')
    detailPlace = fields.Char(string='签到详细地址')
    remark = fields.Char(string='签到备注')
    latitude = fields.Char(string='纬度')
    longitude = fields.Char(string='经度')
    avatar = fields.Char(string='头像url')
