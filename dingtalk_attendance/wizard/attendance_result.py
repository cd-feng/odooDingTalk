# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.addons.dingtalk_base.tools import dingtalk_api


class HrAttendanceResultTransient(models.TransientModel):
    _name = 'hr.attendance.tran'
    _description = '获取钉钉考勤结果'

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_dingding_attendance_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    def get_attendance_list(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，
        钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """

        # 删除已存在的考勤信息
        self.env['hr.attendance.result'].sudo().search([(
            'emp_id', 'in', self.emp_ids.ids), ('work_date', '>=', self.start_date), ('work_date', '<=', self.stop_date)]).unlink()

        logging.info(">>>开始获取员工打卡信息...")
        user_list = list()
        for emp in self.emp_ids:
            if not emp.ding_id:
                raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(emp.name))
            user_list.append(emp.ding_id)
        user_list = dingtalk_api.list_cut(user_list, 50)
        for u in user_list:
            logging.info(">>>开始获取{}员工段数据".format(u))
            date_list = dingtalk_api.day_cut(self.start_date, self.stop_date, 7)
            for d in date_list:
                self.start_pull_attendance_list(d[0], d[1], u)
        logging.info(">>>根据日期获取员工打卡信息结束...")
        return {'type': 'ir.actions.act_window_close'}

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
        din_client = dingtalk_api.get_client(obj=self)
        try:
            result = din_client.attendance.list(data.get('workDateFrom'), data.get('workDateTo'),
                                                user_ids=data.get('userIdList'), offset=data.get('offset'), limit=data.get('limit'))
            if result.get('errcode') == 0:
                data_list = list()
                for rec in result.get('recordresult'):
                    data = {
                        'record_id': rec.get('id'),
                        'work_date': dingtalk_api.timestamp_to_local_date(rec.get('workDate')),  # 工作日
                        'timeResult': rec.get('timeResult'),  # 时间结果
                        'locationResult': rec.get('locationResult'),  # 考勤结果
                        'baseCheckTime': dingtalk_api.timestamp_to_local_date(rec.get('baseCheckTime')),  # 基准时间
                        'sourceType': rec.get('sourceType'),  # 数据来源
                        'check_type': rec.get('checkType'),
                        'check_in': dingtalk_api.timestamp_to_local_date(rec.get('userCheckTime')),
                        'approveId': rec.get('approveId'),
                        'procInstId': rec.get('procInstId'),
                        'ding_plan_id': rec.get('planId'),
                    }
                    if rec.get('procInstId'):
                        result = din_client.bpms.processinstance_get(rec.get('procInstId'))
                        data.update({'procInst_title': result.get('title')})
                    groups = self.env['dingtalk.simple.groups'].sudo().search(
                        [('group_id', '=', rec.get('groupId'))], limit=1)
                    data.update({'ding_group_id': groups[0].id if groups else False})
                    # 员工
                    emp_id = self.env['hr.employee'].sudo().search([('ding_id', '=', rec.get('userId'))], limit=1)
                    data.update({'emp_id': emp_id[0].id if emp_id else False})
                    # 班次
                    plan = self.env['hr.dingtalk.plan'].sudo().search([('plan_id', '=', rec.get('planId'))], limit=1)
                    data.update({'plan_id': plan[0].id if plan else False})
                    data_list.append(data)
                # 批量存储记录
                self.env['hr.attendance.result'].sudo().create(data_list)
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)

    def clear_attendance(self):
        """
        清除已下载的所有钉钉出勤记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
            delete from hr_attendance_result
        """)
