# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
import time
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.addons.dingtalk_base.tools import dingtalk_api


class HrAttendanceRecordTransient(models.TransientModel):
    _name = 'hr.attendance.record.tran'
    _description = '获取员工打卡详情'

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=str(fields.datetime.now()))
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

    def get_attendance_list(self):
        """
        获取用户打卡详情
        :return:
        """
        # 清除旧数据
        self.env['hr.attendance.record'].sudo().search(
            [('userId', 'in', self.emp_ids.ids), ('workDate', '>=', self.start_date), ('workDate', '<=', self.stop_date)]).unlink()
        logging.info(">>>开始获取用户打卡详情...")
        user_list = list()
        for emp in self.emp_ids:
            if not emp.ding_id:
                raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(emp.name))
            user_list.append(emp.ding_id)
        for user in dingtalk_api.list_cut(user_list, 50):
            logging.info(">>>开始获取{}员工段数据".format(user))
            date_list = dingtalk_api.day_cut(self.start_date, self.stop_date, 7)
            for date_arr in date_list:
                self.start_pull_attendance_list(date_arr[0], date_arr[1], user)
        logging.info(">>>结束用户打卡详情...")
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def start_pull_attendance_list(self, from_date, to_date, user_list):
        """
        准备数据进行拉取打卡详情
        :return:
        """
        logging.info(">>>开始获取{}-{}时间段数据".format(from_date, to_date))
        emp_data = self.get_pull_odoo_dict()
        din_client = dingtalk_api.get_client()
        try:
            result = din_client.attendance.list_record(user_list, from_date, to_date)
            # logging.info(">>>数据返回结果%s", result)
            data_list = list()
            for rec in result:
                data = {
                    'userId': emp_data[rec['userId']],
                    'record_id': rec.get('id'),
                    'ding_plan_id': rec.get('planId'),
                    'workDate': self.timestamp_to_local_date(rec.get('workDate')),  # 工作日
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
                groups = self.env['dingtalk.simple.groups'].sudo().search(
                    [('group_id', '=', rec.get('groupId'))], limit=1)
                data.update({'groupId': groups.id if groups else False})
                # 班次
                plan = self.env['hr.dingtalk.plan'].sudo().search([('plan_id', '=', rec.get('planId'))], limit=1)
                data.update({'planId': plan[0].id if plan else False})
                data_list.append(data)
            # 批量存储记录
            self.env['hr.attendance.record'].sudo().create(data_list)
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
    def timestamp_to_local_date(self, timeNum):
        """
        将13位毫秒时间戳转换为本地日期(+8h)
        :param timeNum:
        :return:
        """
        to_second_timestamp = float(timeNum / 1000)  # 毫秒转秒
        to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
        to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
        to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
        to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
        to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
        return to_str_datetime

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

    def clear_attendance_record(self):
        """
        清除已下载的所有钉钉出勤记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
            delete from hr_attendance_record
        """)