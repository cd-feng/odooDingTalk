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
import json
import logging
import time
import requests
from requests import ReadTimeout
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrAttendanceRecord(models.Model):
    _name = "hr.attendance.record"
    _rec_name = 'userId'
    _description = "员工打卡详情"

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
        ('USER', '用户打卡'),
        ('BOSS', '老板改签'),
        ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'),
        ('AUTO_CHECK', '自动打卡')
    ]

    userId = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    record_id = fields.Char(string='唯一标识')
    groupId = fields.Many2one(comodel_name='dingding.simple.groups', string=u'考勤组', index=True)
    planId = fields.Many2one(comodel_name='hr.dingding.plan', string=u'班次', index=True)
    workDate = fields.Datetime(string=u'工作日', index=True)
    corpId = fields.Char(string='企业ID')
    checkType = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')])
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult, index=True)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    approveId = fields.Char(string='关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    procInstId = fields.Char(string='审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    baseCheckTime = fields.Datetime(string=u'基准时间', help="计算迟到和早退，基准时间")
    userCheckTime = fields.Datetime(string="实际打卡时间", help="实际打卡时间,  用户打卡时间的毫秒数")
    userAddress = fields.Char(string='用户打卡地址')
    userLongitude = fields.Char(string='用户打卡经度')
    userLatitude = fields.Char(string='用户打卡纬度')
    outsideRemark = fields.Text(string='打卡备注')


class HrAttendanceRecordTransient(models.TransientModel):
    _name = 'hr.attendance.record.tran'
    _description = '获取员工打卡详情'

    start_date = fields.Datetime(string=u'开始时间', required=True)
    stop_date = fields.Datetime(string=u'结束时间', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many('hr.employee', string='员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        """
        获取全部钉钉员工
        :return:
        """
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_attendance_list(self):
        """
        获取用户打卡详情
        :return:
        """
        # self.clear_attendance() 
        logging.info(">>>开始获取用户打卡详情...")
        user_list = list()
        for emp in self.emp_ids:
            if not emp.ding_id:
                raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(emp.name))
            user_list.append(emp.ding_id)
        user_list = self.env['hr.attendance.tran'].list_cut(user_list, 50)
        for user in user_list:
            logging.info(">>>开始获取{}员工段数据".format(user))
            date_list = self.env['hr.attendance.tran'].day_cut(self.start_date, self.stop_date, 7)
            for date_arr in date_list:
                self.start_pull_attendance_list(date_arr[0], date_arr[1], user)
        logging.info(">>>结束用户打卡详情...")
        action = self.env.ref('dingding_attendance.hr_attendance_record_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def start_pull_attendance_list(self, from_date, to_date, user_list):
        """
        准备数据进行拉取打卡详情
        :return:
        """
        logging.info(">>>开始获取{}-{}时间段数据".format(from_date, to_date))
        emp_data = self.get_pull_odoo_dict()
        din_client = self.env['dingding.api.tools'].get_client()
        try:
            result = din_client.attendance.list_record(user_list, from_date, to_date)
            # logging.info(">>>数据返回结果%s", result)
            for rec in result:
                data = {
                    'userId': emp_data[rec['userId']],
                    'record_id': rec.get('id'),
                    'workDate': self.get_time_stamp(rec.get('workDate')),  # 工作日
                    'corpId': rec.get('corpId'),  # 企业ID
                    'checkType': rec.get('checkType'),  # 考勤类型
                    'sourceType': rec.get('sourceType'),
                    'timeResult': rec.get('timeResult'),
                    'locationResult': rec.get('locationResult'),
                    'approveId': rec.get('approveId'),
                    'procInstId': rec.get('procInstId'),
                    'baseCheckTime': self.get_time_stamp(rec.get('baseCheckTime')) if "baseCheckTime" in rec else False,
                    'userCheckTime': self.get_time_stamp(rec.get('userCheckTime')),
                    'userAddress': rec.get('userAddress'),
                    'userLongitude': rec.get('userLongitude'),
                    'userLatitude': rec.get('userLatitude'),
                    'outsideRemark': rec.get('outsideRemark'),
                }
                # 考勤组
                groups = self.env['dingding.simple.groups'].sudo().search(
                    [('group_id', '=', rec.get('groupId'))], limit=1)
                data.update({'groupId': groups.id if groups else False})
                # 班次
                plan = self.env['hr.dingding.plan'].sudo().search([('plan_id', '=', rec.get('planId'))], limit=1)
                data.update({'planId': plan[0].id if plan else False})
                attendance = self.env['hr.attendance.record'].sudo().search([('record_id', '=', rec.get('id'))])
                if not attendance:
                    self.env['hr.attendance.record'].sudo().create(data)
        except Exception as e:
            raise UserError(e)
        return True

    @api.model
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间
        :param timeNum:
        :return:
        """
        timeStamp = float(timeNum / 1000)
        timeArray = time.gmtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime

    @api.model
    def get_pull_odoo_dict(self):
        """
        返回准备数据字典
        :return:
        """
        employees = self.env['hr.employee'].sudo().search([('ding_id', '!=', '')])
        emp_data = {}
        for emp in employees:
            emp_data.update({emp.ding_id: emp.id})
        return emp_data

    @api.model
    def clear_attendance(self):
        """
        清除已下载的所有钉钉出勤记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
            delete from hr_attendance_result
        """)