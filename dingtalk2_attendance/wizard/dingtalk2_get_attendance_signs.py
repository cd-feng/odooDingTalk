# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta
import logging
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class Dingtalk2GetAttendanceSigns(models.TransientModel):
    _name = "dingtalk2.get.attendance.signs"
    _description = "获取钉钉签到记录"

    start_date = fields.Date(string="开始日期", required=True)
    end_date = fields.Date(string="截止日期", required=True)

    @staticmethod
    def signs_day_cut(begin_time, end_time, days):
        """
        日期分段
        :param begin_time:开始日期
        :param end_time:结束日期
        :param days: 最大间隔时间
        :return:
        """
        cut_day = []
        begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
        end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
        delta = timedelta(days=days)
        t1 = begin_time
        while t1 <= end_time:
            if end_time < t1 + delta:
                t2 = end_time
            else:
                t2 = t1 + delta
            cut_day.append([dt.get_time_stamp13(t1), dt.get_time_stamp13(t2)])
            t1 = t2 + timedelta(days=1)
        return cut_day

    def on_get(self):
        """
        开始获取记录
        """
        employee_ids = self.env['hr.employee'].sudo().search([('ding_id', '!=', False), ('company_id', '=', self.env.company.id)])
        user_list = []
        user_dict = {}
        for employee_id in employee_ids:
            user_list.append(employee_id.ding_id)
            user_dict[employee_id.ding_id] = employee_id.id
        user_list = dt.list_cut(user_list, 10)
        for user in user_list:
            date_list = self.signs_day_cut(self.start_date, self.end_date, 7)
            for d in date_list:
                self.start_pull_attendance_signs(d[0], d[1], user, self.env.company, user_dict)

    @api.model
    def start_pull_attendance_signs(self, start_date, end_date, user_list, company, user_dict):
        """
        准备数据进行拉取签到记录
        :return:
        """
        logging.info(">>>开始获取{}-{}时间段数据".format(start_date, end_date))
        cursor = 0
        size = 100
        while True:
            data = {
                'start_time': start_date,
                'end_time': end_date,
                'userid_list': ",".join(x for x in user_list),
                'cursor': cursor,
                'size': size,
            }
            next_cursor = self.send_post_dingtalk(data, company, user_dict)
            logging.info(">>>是否还有剩余数据：{}".format(next_cursor))
            if not next_cursor:
                break
            else:
                cursor = next_cursor

    @api.model
    def send_post_dingtalk(self, data, company, user_dict):
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company))
        signs_model = self.env['dingtalk2.attendance.signs'].sudo()
        try:
            req_result = client.post('topapi/checkin/record/get', data)
            if req_result.get('errcode') == 0:
                result = req_result.get('result')
                value_list = []
                for rec in result.get('page_list'):
                    value_list.append({
                        'company_id': company.id,
                        'checkin_time': dt.get_time_stamp(rec.get('checkin_time')),
                        'detail_place': rec.get('detail_place'),
                        'remark': rec.get('remark'),
                        'name': user_dict.get(rec.get('userid')),
                        'place': rec.get('place'),
                        'visit_user': rec.get('visit_user'),
                    })
                signs_model.create(value_list)
                return result.get('next_cursor')
            else:
                raise exceptions.ValidationError('请求失败,errmsg:{}'.format(req_result.get('errmsg')))
        except Exception as e:
            raise exceptions.ValidationError(e)

