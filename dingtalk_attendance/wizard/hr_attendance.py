# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020 SuXueFeng GNU
###################################################################################

import logging
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.addons.dingtalk_base.tools import dingtalk_api
_logger = logging.getLogger()


class GetHrAttendanceResult(models.TransientModel):
    _name = 'get.hr.attendance.result'
    _description = '获取钉钉考勤结果'

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=fields.Date.context_today)
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingtalk_hr_attendance_result_rel',
                               string=u'员工', required=True, domain="[('ding_id', '!=', '')]")
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            self.emp_ids = [(6, 0, emps.ids)]

    def get_attendance_result(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，
        钉钉限制每次传递员工数最大为50个
        :return:
        """
        # 删除已存在的考勤信息
        domain = [('employee_id', 'in', self.emp_ids.ids), ('work_date', '>=', self.start_date), ('work_date', '<=', self.stop_date)]
        self.env['hr.attendance'].sudo().search(domain).unlink()
        user_list = list()
        for emp in self.emp_ids:
            user_list.append(emp.ding_id)
        user_list = dingtalk_api.list_cut(user_list, 50)
        for u in user_list:
            _logger.debug(">>>开始获取{}员工段数据".format(u))
            date_list = dingtalk_api.day_cut(self.start_date, self.stop_date, 7)
            for d in date_list:
                self.start_pull_attendance_list(d[0], d[1], u)
        _logger.debug(">>>根据日期获取员工打卡信息结束...")
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def start_pull_attendance_list(self, from_date, to_date, user_list):
        """
        准备数据进行拉取考勤结果
        :return:
        """
        _logger.debug(">>>开始获取{}-{}时间段数据".format(from_date, to_date))
        offset = 0
        limit = 50
        while True:
            data = {
                'workDateFrom': from_date,
                'workDateTo': to_date,
                'userIdList': user_list,
                'offset': offset,
                'limit': limit,
            }
            has_more = self.send_post_dingtalk(data)
            _logger.debug(">>>是否还有剩余数据：{}".format(has_more))
            if not has_more:
                break
            else:
                offset = offset + limit
                _logger.debug(">>>准备获取剩余数据中的第{}至{}条".format(offset + 1, offset + limit))
        return True

    @api.model
    def send_post_dingtalk(self, data):
        ding_client = dingtalk_api.get_client(self)
        try:
            result = ding_client.attendance.list(data.get('workDateFrom'), data.get('workDateTo'),
                                                user_ids=data.get('userIdList'), offset=data.get('offset'), limit=data.get('limit'))
            if result.get('errcode') == 0:
                for rec in result.get('recordresult'):
                    emp_id = self.env['hr.employee'].sudo().search([('ding_id', '=', rec.get('userId'))], limit=1)
                    groups = self.env['dingtalk.simple.groups'].search([('group_id', '=', rec.get('groupId'))], limit=1)
                    work_date = dingtalk_api.datetime_local_data(rec.get('workDate'), is_date=True)
                    check_in = dingtalk_api.timestamp_to_local_date(self, rec.get('userCheckTime'))
                    # 上班卡
                    if rec.get('checkType') == 'OnDuty':
                        attendance_data = {
                            'employee_id': emp_id.id,  # 员工
                            'ding_group_id': groups.id if groups else False,  # 钉钉考勤组
                            'ding_plan_id': rec.get('planId'),                # 钉钉排班ID
                            'work_date': work_date,                           # 工作日
                            'check_in': check_in,                             # 签到时间
                        }
                        self.env['hr.attendance'].create(attendance_data)
                    elif rec.get('checkType') == 'OffDuty':
                        domain = [('employee_id', '=', emp_id.id), ('work_date', '=', work_date)]
                        attendance = self.env['hr.attendance'].search(domain)
                        if attendance:
                            attendance.write({
                                'check_out': check_in,                 # 迁出时间
                                'time_result': rec.get('timeResult'),  # 时间结果
                                'source_type': rec.get('sourceType'),  # 数据来源
                            })
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)