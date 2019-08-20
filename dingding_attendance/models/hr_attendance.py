# -*- coding: utf-8 -*-
import logging
import time
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = "Attendance"

    TimeResult = [
        ('Normal', '正常'),
        ('Early', '早退'),
        ('Late', '迟到'),
        ('SeriousLate', '严重迟到'),
        ('Absenteeism', '旷工迟到'),
        ('NotSigned', '未打卡'),
    ]
    LocationResult = [
        ('Normal', '范围内'), ('Outside', '范围外'), ('NotSigned', '未打卡'),
    ]
    SourceType = [
        ('ATM', '考勤机'),
        ('BEACON', 'IBeacon'),
        ('DING_ATM', '钉钉考勤机'),
        ('USER', '手机打卡'),
        ('BOSS', '管理员改签'),
        ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'),
        ('AUTO_CHECK', '自动打卡'),
        ('odoo', 'Odoo系统'),
    ]
    ding_group_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'钉钉考勤组')
    workDate = fields.Datetime(string=u'工作日')
    on_timeResult = fields.Selection(string=u'上班考勤结果', selection=TimeResult)
    off_timeResult = fields.Selection(string=u'下班考勤结果', selection=TimeResult)
    on_planId = fields.Char(string=u'上班班次ID')
    off_planId = fields.Char(string=u'下班班次ID')
    on_sourceType = fields.Selection(string=u'上班数据来源', selection=SourceType)
    off_sourceType = fields.Selection(string=u'下班数据来源', selection=SourceType)

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """
        取消系统自带验证出勤记录的有效性的验证
        :return:
        """
        return True


class HrAttendanceTransient(models.TransientModel):
    _name = 'hr.attendance.tran.v2'
    _description = '获取钉钉考勤信息'

    start_date = fields.Datetime(string=u'开始日期', required=True)
    stop_date = fields.Datetime(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_dingtalk_attendance_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_attendance_list_v2(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，
        钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        # self.clear_attendance()
        logging.info(">>>开始获取员工打卡信息...")
        user_list = list()
        for emp in self.emp_ids:
            if not emp.ding_id:
                raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(emp.name))
            user_list.append(emp.ding_id)
        user_list = self.env['hr.attendance.tran'].list_cut(user_list, 50)
        for u in user_list:
            logging.info(">>>开始获取{}员工段数据".format(u))
            date_list = self.env['hr.attendance.tran'].day_cut(self.start_date, self.stop_date, 7)
            for d in date_list:
                self.start_pull_attendance_list(d[0], d[1], u)
        logging.info(">>>根据日期获取员工打卡信息结束...")
        # 刷新数据并重新载入考勤列表
        action = self.env.ref('hr_attendance.hr_attendance_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def start_pull_attendance_list(self, from_date, to_date, user_list):
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
            has_more = self.send_post_dindin(data)
            logging.info(">>>是否还有剩余数据：{}".format(has_more))
            if not has_more:
                break
            else:
                offset = offset + limit
                logging.info(">>>准备获取剩余数据中的第{}至{}条".format(offset + 1, offset + limit))
        return True

    @api.model
    def send_post_dindin(self, data):
        din_client = self.env['dingding.api.tools'].get_client()
        try:
            result = din_client.attendance.list(data.get('workDateFrom'), data.get('workDateTo'),
                                                user_ids=data.get('userIdList'), offset=data.get('offset'), limit=data.get('limit'))
            # logging.info(">>>获取考勤结果%s", result)
            if result.get('errcode') == 0:
                OnDuty_list = list()
                OffDuty_list = list()
                for rec in result.get('recordresult'):
                    data = {
                        'workDate': self.get_time_stamp(rec.get('workDate')),  # 工作日
                    }
                    groups = self.env['dingding.simple.groups'].sudo().search(
                        [('group_id', '=', rec.get('groupId'))], limit=1)
                    data.update({'ding_group_id': groups[0].id if groups else False})
                    emp_id = self.env['hr.employee'].sudo().search([('ding_id', '=', rec.get('userId'))], limit=1)
                    data.update({'employee_id': emp_id[0].id if emp_id else False})
                    if rec.get('checkType') == 'OnDuty':
                        data.update(
                            {'check_in': self.get_time_stamp(rec.get('userCheckTime')),
                             'on_planId': rec.get('planId'),
                             'on_timeResult': rec.get('timeResult'),
                             'on_sourceType': rec.get('sourceType')
                             })
                        OnDuty_list.append(data)
                    else:
                        data.update({
                            'check_out': self.get_time_stamp(rec.get('userCheckTime')),
                            'off_planId': rec.get('planId'),
                            'off_timeResult': rec.get('timeResult'),
                            'off_sourceType': rec.get('sourceType')
                        })
                        OffDuty_list.append(data)
                # 上班考勤结果列表与下班考勤结果列表按时间排序后合并
                OnDuty_list.sort(key=lambda x: (x['employee_id'], x['check_in']))
                # logging.info(">>>获取OnDuty_list结果%s", OnDuty_list)
                OffDuty_list.sort(key=lambda x: (x['employee_id'], x['check_out']))
                # logging.info(">>>获取OffDuty_list结果%s", OffDuty_list)
                duty_list = list()
                on_planId_list = list()
                for onduty in OnDuty_list:
                    for offduty in OffDuty_list:
                        datetime_check_out = datetime.strptime(offduty.get('check_out'), "%Y-%m-%d %H:%M:%S")
                        datetime_check_in = datetime.strptime(onduty.get('check_in'), "%Y-%m-%d %H:%M:%S")
                        if int(offduty.get('off_planId')) == int(onduty.get('on_planId')) + 1 and \
                                offduty.get('employee_id') == onduty.get('employee_id') and \
                                offduty.get('workDate') == onduty.get('workDate'):
                            duty_tmp = dict(onduty, **offduty)
                            duty_list.append(duty_tmp)
                            on_planId_list.append(onduty.get('on_planId'))
                        elif datetime_check_out > datetime_check_in and \
                                offduty.get('employee_id') == onduty.get('employee_id') and \
                                offduty.get('workDate') == onduty.get('workDate') and \
                                onduty.get('on_planId') not in on_planId_list:
                            duty_tmp = dict(onduty, **offduty)
                            duty_list.append(duty_tmp)
                            on_planId_list.append(onduty.get('on_planId'))

                # 将合并的考勤导入odoo考勤
                duty_list.sort(key=lambda x: (x['employee_id'], x['check_in']))
                logging.info(">>>获取duty_list结果%s", duty_list)
                for att in duty_list:
                    attendance = self.env['hr.attendance'].sudo().search(
                        [('employee_id', '=', att.get('employee_id')),
                            ('on_planId', '=', att.get('on_planId'))])
                    if not attendance:
                        self.env['hr.attendance'].sudo().create(att)
                    else:
                        attendance.sudo().write({
                            'check_in': att.get('check_in'),
                            'on_planId': att.get('on_planId'),
                            'on_timeResult': att.get('on_timeResult'),
                            'on_sourceType': att.get('on_sourceType'),
                            'check_out': att.get('check_out'),
                            'off_planId': att.get('off_planId'),
                            'off_timeResult': att.get('off_timeResult'),
                            'off_sourceType': att.get('off_sourceType')
                        })
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)

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

    @api.multi
    def get_attendance_list_sync(self):
        """
        每隔1小时自动下载钉钉全员考勤记录
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        logging.info(">>>开始获取员工打卡信息...")
        employees = self.env['hr.employee'].sudo().search([('ding_id', '!=', '')])
        emp_list = list()
        for emp in employees:
            emp_list.append(emp.ding_id)
        user_list = self.env['hr.attendance.tran'].list_cut(emp_list, 50)
        for u in user_list:
            offset = 0
            limit = 50
            while True:
                data = {
                    'workDateFrom': str(fields.datetime.now() - timedelta(hours=1)),  # 开始日期
                    'workDateTo': str(fields.datetime.now()),  # 结束日期
                    'userIdList': u,  # 员工列表
                    'offset': offset,
                    'limit': limit,
                }
                has_more = self.send_post_dindin(data)

                if not has_more:
                    break
                else:
                    offset = offset + limit
        logging.info(">>>根据日期获取员工打卡信息结束...")
