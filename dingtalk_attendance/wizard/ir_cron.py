# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class AttendanceIrCronTask(models.TransientModel):
    _name = 'dingtalk.attendance.cron.task'
    _description = '定时获取钉钉考勤信息任务'

    def start_task(self):
        """
        开始任务
        :return:
        """
        _logger.info(">>>Start attendance task")
        emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
        user_list = list()
        for emp in emps:
            user_list.append(emp.ding_id)
        dt_attendance_interval_type = self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_attendance_interval_type')
        start_date = fields.date.today()   # 开始日期
        end_date = fields.date.today()     # 结束日期
        if dt_attendance_interval_type == 'days':
            start_date = start_date - relativedelta(days=1)
        elif dt_attendance_interval_type == 'weeks':
            start_date = start_date - relativedelta(days=7)
        else:
            start_date = start_date - relativedelta(months=1)
        # 清除旧数据
        domain = [('userId', 'in', emps.ids), ('userCheckTime', '>=', start_date), ('userCheckTime', '<=', end_date)]
        domain2 = [('emp_id', 'in', emps.ids), ('check_in', '>=', start_date), ('check_in', '<=', end_date)]
        domain3 = [('employee_id', 'in', emps.ids), ('work_date', '>=', start_date), ('work_date', '<=', end_date)]
        self.env['hr.attendance.record'].sudo().search(domain).unlink()
        self.env['hr.attendance.result'].sudo().search(domain2).unlink()
        self.env['hr.attendance'].sudo().search(domain3).unlink()
        date_list = dingtalk_api.day_cut(start_date, end_date, 7)
        for user in dingtalk_api.list_cut(user_list, 50):
            for date_line in date_list:
                # 打卡详情
                # self.env['hr.attendance.record.tran'].start_pull_attendance_list(date_line[0], date_line[1], user)
                # 打卡结果
                # self.env['hr.attendance.tran'].start_pull_attendance_list(date_line[0], date_line[1], user)
                # 原生打考勤列表
                self.env['get.hr.attendance.result'].start_pull_attendance_list(date_line[0], date_line[1], user)
        _logger.info(">>>Stop attendance task")
        return
