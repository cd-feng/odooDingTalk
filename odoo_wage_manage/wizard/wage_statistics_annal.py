# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WageEmpAttendanceAnnal(models.TransientModel):
    _description = '计算考勤结果'
    _name = 'wage.employee.attendance.annal.transient'

    SourceType = [
        ('dingding', '钉钉考勤结果'),
        ('odoo', 'Odoo出勤记录'),
        ('and', '两者同时获取')
    ]

    soure_type = fields.Selection(string=u'考勤结果来源', selection=SourceType, default='odoo', required=True)
    start_date = fields.Date(string=u'考勤开始日期', required=True)
    end_date = fields.Date(string=u'考勤结束日期', required=True)

    @api.multi
    def compute_attendance_result(self):
        """
        立即计算考勤结果
        :return:
        """
        self.ensure_one()
        raise UserError("暂未实现！！！")


class WageEmpPerformanceManage(models.TransientModel):
    _description = '从绩效计算结果'
    _name = 'wage.employee.performance.manage.transient'

    start_date = fields.Date(string=u'开始日期', required=True)
    end_date = fields.Date(string=u'结束日期', required=True)

    @api.multi
    def compute_performance_result(self):
        """
        从绩效计算结果
        :return:
        """
        self.ensure_one()
        raise UserError("暂未实现！！！")
