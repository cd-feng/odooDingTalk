# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, exceptions
import logging
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class Dingtalk2GetAttendanceList(models.TransientModel):
    _name = "dingtalk2.get.attendance.list"
    _description = "获取考勤打卡结果"

    start_date = fields.Date(string="开始日期", required=True)
    end_date = fields.Date(string="截止日期", required=True)

    def get_ding_employee(self, company_id=None):
        """
        返回所有的钉钉员工
        """
        if not company_id:
            company_id = self.env.company.id
        return self.env['hr.employee'].sudo().search([('ding_id', '!=', False), ('company_id', '=', company_id)])

    def on_get(self):
        """
        开始获取考勤打卡结果
        """
        user_list = []
        user_dict = {}
        for employee_id in self.get_ding_employee():
            user_list.append(employee_id.ding_id)
            user_dict[employee_id.ding_id] = employee_id.id
        user_list = dt.list_cut(user_list, 50)
        for user in user_list:
            date_list = dt.day_cut(self.start_date, self.end_date, 7)
            for d in date_list:
                self.start_pull_attendance_list(d[0], d[1], user, self.env.company, user_dict)

    @api.model
    def start_pull_attendance_list(self, start_date, end_date, user_list, company, user_dict):
        """
        准备数据进行拉取考勤结果
        :return:
        """
        logging.info(">>>开始获取{}-{}时间段数据".format(start_date, end_date))
        offset = 0
        limit = 50
        while True:
            data = {
                'workDateFrom': start_date,
                'workDateTo': end_date,
                'userIdList': user_list,
                'offset': offset,
                'limit': limit,
            }
            has_more = self.send_post_dingtalk(data, company, user_dict)
            logging.info(">>>是否还有剩余数据：{}".format(has_more))
            if not has_more:
                break
            else:
                offset = offset + limit
                logging.info(">>>准备获取剩余数据中的第{}至{}条".format(offset + 1, offset + limit))

    @api.model
    def send_post_dingtalk(self, data, company, user_dict):
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company))
        attendance_model = self.env['dingtalk2.attendance.list'].sudo()
        try:
            result = client.post('attendance/list', data)
            if result.get('errcode') == 0:
                for rec in result.get('recordresult'):
                    value = {
                        'company_id': company.id,
                        'source_type': rec.get('sourceType'),
                        'base_check_time': dt.get_time_stamp(rec.get('baseCheckTime')),  # 基准时间
                        'user_check_time': dt.get_time_stamp(rec.get('userCheckTime')),
                        'location_result': rec.get('locationResult'),
                        'time_result': rec.get('timeResult'),
                        'check_type': rec.get('checkType'),
                        'name': user_dict.get(rec.get('userId')),
                        'work_date': dt.timestamp_to_local_date(self, rec.get('workDate')),  # 工作日
                        'record_id': rec.get('recordId'),
                        'plan_id': rec.get('planId'),
                        'group_id': rec.get('groupId'),
                        'ding_id': rec.get('id'),
                    }
                    domain = [('record_id', '=', rec.get('recordId'))]
                    attendance_res = attendance_model.search(domain)
                    if attendance_res:
                        attendance_res.write(value)
                    else:
                        attendance_model.create(value)
                return result.get('hasMore')
            else:
                raise exceptions.ValidationError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise exceptions.ValidationError(e)

    @api.model
    def auto_get_attendance_list(self):
        """
        定时任务： 同步每天的考勤结果
        """
        start_date = datetime.date.today()
        end_date = datetime.date.today()
        for config_id in self.env['dingtalk2.config'].search([]):
            user_list = []
            user_dict = {}
            for employee_id in self.get_ding_employee(config_id.company_id.id):
                user_list.append(employee_id.ding_id)
                user_dict[employee_id.ding_id] = employee_id.id
            user_list = dt.list_cut(user_list, 50)
            for user in user_list:
                date_list = dt.day_cut(start_date, end_date, 7)
                for d in date_list:
                    self.start_pull_attendance_list(d[0], d[1], user, config_id.company_id, user_dict)

