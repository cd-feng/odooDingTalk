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


class DinDinUsersSign(models.Model):
    _name = 'dindin.users.signs'
    _description = "用户签到记录"
    _rec_name = 'start_time'

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='users_sign_and_employee_to_rel',
                               column1='sign_id', column2='emp_id', string=u'员工', required=True)
    start_time = fields.Datetime(string=u'开始时间', required=True)
    end_time = fields.Datetime(string=u'结束时间', required=True)
    line_ids = fields.One2many(comodel_name='dindin.users.signs.line', inverse_name='signs_id', string=u'列表')

    @api.multi
    def find_users_sign(self):
        """获取用户签到记录"""
        logging.info(">>>获取用户签到记录...")
        for res in self:
            res.line_ids = False
            url = self.env['dingding.parameter'].search([('key', '=', 'get_user_checkin')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            start_time = datetime.datetime.strptime("{}.42".format(str(res.start_time)),
                                                    "%Y-%m-%d %H:%M:%S.%f").timetuple()
            end_time = datetime.datetime.strptime("{}.42".format(str(res.end_time)), "%Y-%m-%d %H:%M:%S.%f").timetuple()
            user_str = ''
            for user in self.emp_ids:
                if user_str == '':
                    user_str = user_str + "{}".format(user.ding_id)
                else:
                    user_str = user_str + ",{}".format(user.ding_id)
            data = {
                'userid_list': user_str,
                'start_time': "{}000".format(int(time.mktime(start_time))),
                'end_time': "{}000".format(int(time.mktime(end_time))),
                'cursor': 0,
                'size': 100,
            }
            try:
                result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    line_list = list()
                    r_result = result.get('result')
                    for data in r_result.get('page_list'):
                        emp = self.env['hr.employee'].sudo().search([('ding_id', '=', data.get('userid'))])
                        line_list.append({
                            'emp_id': emp.id if emp else False,
                            'checkin_time': self.get_time_stamp(data.get('checkin_time')),
                            'place': data.get('place'),
                            'detail_place': data.get('detail_place'),
                            'remark': data.get('remark'),
                            'latitude': data.get('latitude'),
                            'longitude': data.get('longitude'),
                        })
                    res.line_ids = line_list
                else:
                    raise UserError("获取失败,原因:{}，\r\n如果是取1个人的数据，时间范围最大到10天，\r\n如果是取多个人的数据，时间范围最大1天。".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("获取用户签到记录网络连接超时")

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


class DinDinUsersSignLine(models.Model):
    _name = 'dindin.users.signs.line'
    _description = "用户签到记录列表"
    _rec_name = 'emp_id'

    signs_id = fields.Many2one(comodel_name='dindin.users.signs', string=u'签到', ondelete='cascade')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    checkin_time = fields.Datetime(string=u'签到时间')
    place = fields.Char(string='签到地址')
    detail_place = fields.Char(string='签到详细地址')
    remark = fields.Char(string='签到备注')
    latitude = fields.Char(string='纬度')
    longitude = fields.Char(string='经度')
    visit_user = fields.Char(string='拜访对象')
