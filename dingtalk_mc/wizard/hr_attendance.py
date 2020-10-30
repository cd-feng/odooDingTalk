# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020 SuXueFeng GNU
###################################################################################

import logging
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt
_logger = logging.getLogger()


class HrAttendanceResultTransient(models.TransientModel):
    _name = 'hr.attendance.tran'
    _description = '获取钉钉考勤结果'

    company_ids = fields.Many2many("res.company", string="公司", required=True, default=lambda self: self.env.ref('base.main_company'))
    start_date = fields.Date(string=u'开始日期', required=True, default=fields.Date.context_today)
    stop_date = fields.Date(string=u'结束日期', required=True, default=fields.Date.context_today)

    def get_attendance_list(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，
        钉钉限制每次传递员工数最大为50个
        :return:
        """
        self.ensure_one()
        _logger.info(">>>开始获取打卡结果...")
        for company in self.company_ids:
            # 获取该公司下所有员工
            emp_ids = self.env['hr.employee'].search([('ding_id', '!=', ''), ('company_id', '=', company.id)])
            domain = [('employee_id', 'in', emp_ids.ids), ('work_date', '>=', self.start_date), ('work_date', '<=', self.stop_date)]
            # 删除已存在的考勤信息
            self.env['hr.attendance.result'].search(domain).unlink()
            user_list = list()
            for emp in emp_ids:
                user_list.append(emp.ding_id)
            user_list = dt.list_cut(user_list, 50)
            for user in user_list:
                date_list = dt.day_cut(self.start_date, self.stop_date, 7)
                for d in date_list:
                    self.start_pull_attendance_list(d[0], d[1], user, company)
        _logger.info(">>>获取打卡信息结束...")
        return {'type': 'ir.actions.act_window_close'}

    def start_pull_attendance_list(self, from_date, to_date, user_list, company):
        """
        准备数据进行拉取考勤结果
        :return:
        """
        logging.info(">>>开始获取{}-{}时间段数据".format(from_date, to_date))
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
            has_more = self.send_post_dingtalk(data, company)
            logging.info(">>>是否还有剩余数据：{}".format(has_more))
            if not has_more:
                break
            else:
                offset = offset + limit
                logging.info(">>>准备获取剩余数据中的第{}至{}条".format(offset + 1, offset + limit))
        return True

    def send_post_dingtalk(self, data, company):
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            result = client.attendance.list(data.get('workDateFrom'), data.get('workDateTo'),
                                            user_ids=data.get('userIdList'), offset=data.get('offset'), limit=data.get('limit'))
            if result.get('errcode') == 0:
                data_list = list()
                for rec in result.get('recordresult'):
                    # 员工
                    emp_id = self.env['hr.employee'].sudo().search([('ding_id', '=', rec.get('userId')), ('company_id', '=', company.id)], limit=1)
                    data_list.append({
                        'company_id': company.id,
                        'employee_id': emp_id.id if emp_id else False,
                        'work_date': dt.timestamp_to_local_date(rec.get('workDate'), self),  # 工作日
                        'record_id': rec.get('id'),
                        'check_type': rec.get('checkType'),
                        'timeResult': rec.get('timeResult'),  # 时间结果
                        'locationResult': rec.get('locationResult'),  # 考勤结果
                        'baseCheckTime': dt.get_time_stamp(rec.get('baseCheckTime')),  # 基准时间
                        'check_in': dt.get_time_stamp(rec.get('userCheckTime')),
                        'sourceType': rec.get('sourceType'),  # 数据来源
                    })
                self.env['hr.attendance.result'].sudo().create(data_list)
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)

    @api.model
    def get_users_attendance_data(self):
        """
        定时任务-获取考勤数据
        :return:
        """
        # 获取考勤公司
        configs = self.env['dingtalk.mc.config'].search([('cron_attendance', '=', True)])
        start_date = fields.date.today()  # 开始日期
        end_date = fields.date.today()  # 结束日期
        start_date = start_date - relativedelta(days=2)
        for config in configs:
            company = config.company_id
            try:
                # 获取该公司下所有员工
                emp_ids = self.env['hr.employee'].search([('ding_id', '!=', ''), ('company_id', '=', company.id)])
                domain = [('employee_id', 'in', emp_ids.ids), ('work_date', '>=', start_date), ('work_date', '<=', end_date)]
                # 删除已存在的考勤信息
                self.env['hr.attendance.result'].search(domain).unlink()
                user_list = list()
                for emp in emp_ids:
                    user_list.append(emp.ding_id)
                user_list = dt.list_cut(user_list, 50)
                for user in user_list:
                    date_list = dt.day_cut(start_date, end_date, 7)
                    for d in date_list:
                        self.start_pull_attendance_list(d[0], d[1], user, company)
            except Exception as e:
                _logger.info(">>>{}-同步考勤数据失败，失败原因：{}".format(company.name, e))
                continue


class CalculateMonthAttendance(models.TransientModel):
    _name = 'calculate.month.attendance'
    _description = '计算考勤统计'
    _rec_name = 'start_date'

    company_ids = fields.Many2many("res.company", string="公司", required=True, default=lambda self: self.env.ref('base.main_company'))
    start_date = fields.Date(string=u'开始日期', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string=u'结束日期', required=True, default=fields.Date.context_today)

    def calculate_attendance(self):
        """
        计算结果
        :return:
        """
        self.ensure_one()
        month_code = "{}/{}".format(str(self.start_date)[:4], str(self.start_date)[5:7])
        for company in self.company_ids:
            # 获取公司员工
            emp_ids = self.env['hr.employee'].search([('ding_id', '!=', ''), ('company_id', '=', company.id)])
            for emp in emp_ids:
                domain = [('employee_id', '=', emp.id), ('company_id', '=', company.id),
                          ('work_date', '>=', str(self.start_date)), ('work_date', '<=', str(self.end_date))]
                # 读取考勤结果表
                results = self.env['hr.attendance.result'].search(domain)
                if not results:
                    continue
                normal_count = early_count = late_count = absenteeism_count = signed_count = 0.0
                # 正常打卡        早退次数     迟到次数        旷工次数              未打卡次数
                for result in results:
                    if result.timeResult == 'Normal':  # 正常
                        normal_count += 0.5
                    elif result.timeResult == 'Early':  # 早退
                        early_count += 0.5
                    elif result.timeResult in ('Late', 'SeriousLate'):  # 迟到
                        late_count += 0.5
                    elif result.timeResult == 'Absenteeism':  # 旷工迟到
                        absenteeism_count += 0.5
                    else:
                        signed_count += 0.5
                data = {
                    'company_id': company.id,
                    'employee_id': emp.id,
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'normal_count': normal_count,
                    'early_count': early_count,
                    'late_count': late_count,
                    'absenteeism_count': absenteeism_count,
                    'signed_count': signed_count,
                }
                result = self.env['hr.month.attendance'].search([('month_code', '=', month_code), ('employee_id', '=', emp.id)])
                if result:
                    result.write(data)
                else:
                    self.env['hr.month.attendance'].create(data)


class DingtalkUsersDuration(models.TransientModel):
    _name = 'dingtalk.users.duration'
    _description = '员工预计算时长'

    company_ids = fields.Many2many("res.company", string="公司", required=True, default=lambda self: self.env.ref('base.main_company'))
    duration_type = fields.Selection(string="计算方法", selection=[('0', '按自然日计算'), ('1', '按工作日计算')], default='1')
    start_date = fields.Date(string=u'开始日期', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string=u'结束日期', required=True, default=fields.Date.context_today)
    is_overtime = fields.Boolean(string="加班", default=True)
    is_travel = fields.Boolean(string="出差", default=True)
    is_leave = fields.Boolean(string="请假", default=True)

    def calculate_duration(self):
        """
        计算员工预计算时长
        :return:
        """
        self.ensure_one()
        start_date = str(self.start_date)
        end_date = str(self.end_date)
        duration_type = int(self.duration_type)
        for company in self.company_ids:
            # 获取该公司下所有员工
            emp_ids = self.env['hr.employee'].search([('ding_id', '!=', ''), ('company_id', '=', company.id)])
            for emp in emp_ids:
                # 加班
                if self.is_overtime:
                    self.get_user_duration(company, emp, 1, start_date, end_date, duration_type)
                # 出差
                if self.is_travel:
                    self.get_user_duration(company, emp, 2, start_date, end_date, duration_type)
                # 请假
                if self.is_leave:
                    self.get_user_duration(company, emp, 3, start_date, end_date, duration_type)

    def get_user_duration(self, company, emp, biz_type, from_time, to_time, duration_type):
        """
        获取预计算时长
        :param company: 公司
        :param emp:     员工
        :param biz_type:  1：加班，2：出差，3：请假
        :param from_time: 起始日期
        :param to_time:   结束日期
        :param duration_type: 0：按自然日计算；1：按工作日计算
        :return:
        """
        month_code = "{}/{}".format(from_time[:4], from_time[5:7])
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            result = client.post('/topapi/attendance/approve/duration/calculate', {
                'userid': emp.ding_id,
                'biz_type': biz_type,  # 1：加班，2：出差，3：请假
                'from_time': from_time,
                'to_time': to_time,
                'duration_unit': 'day',
                'calculate_model': duration_type,   # 0：按自然日计算；1：按工作日计算
            })
        except Exception as e:
            raise UserError(e)
        if result.get('errcode') == 0:
            result = result.get('result')
            duration = result.get('duration')
            new_data = {
                'company_id': company.id,
                'employee_id': emp.id,
                'start_date': from_time,
                'end_date': to_time,
            }
            domain = [('employee_id', '=', emp.id), ('month_code', '=', month_code)]
            emp_month = self.env['hr.month.attendance'].search(domain)
            if biz_type == 1:
                if emp_month:
                    emp_month.write({'overtime_days': duration})
                else:
                    new_data.update({'overtime_days': duration})
                    self.env['hr.month.attendance'].create(new_data)
            elif biz_type == 2:
                if emp_month:
                    emp_month.write({'travel_days': duration})
                else:
                    new_data.update({'travel_days': duration})
                    self.env['hr.month.attendance'].create(new_data)
            elif biz_type == 3:
                if emp_month:
                    emp_month.write({'leave_days': duration})
                else:
                    new_data.update({'leave_days': duration})
                    self.env['hr.month.attendance'].create(new_data)
