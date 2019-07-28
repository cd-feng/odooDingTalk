# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
import datetime
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class DingdingAttendanceIrCron(models.TransientModel):
    _description = '钉钉考勤自动任务'
    _name = 'dingding.attendance.ir.cron'

    @api.model
    def start_yun_attendance_cron(self):
        """
        依次执行考勤自动任务
        :return:
        """
        logging.info(">>>---------------Start Dingding Attendance Cron------------")
        # 自动拉取当天的下一天的排班信息
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        try:
            self.env['hr.dingding.plan.tran'].sudo().start_pull_plan_lists(work_date=str(tomorrow))
        except Exception as e:
            logging.info(">>>拉取排班信息失败,原因:{}".format(str(e)))
        # 自动同步上二天的考勤结果数据
        yesterday = today - datetime.timedelta(days=2)
        employees = self.env['hr.employee'].search([('ding_id', '!=', '')])
        employee_list = list()
        for emp in employees:
            employee_list.append(emp.ding_id)
        user_cut_list = self.env['hr.attendance.tran'].list_cut(employee_list, 50)
        try:
            from_date = "{} 00:00:00".format(str(yesterday))
            to_date = "{} 00:00:00".format(str(today))
            for user_list in user_cut_list:
                self.env['hr.attendance.tran'].sudo().start_pull_attendance_list(from_date, to_date, user_list)
        except Exception as e:
            logging.info(">>>拉取考勤结果数据失败,原因:{}".format(str(e)))
        logging.info(">>>---------------END Dingding Attendance Cron--------------")

