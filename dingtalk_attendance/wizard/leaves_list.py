# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.addons.dingtalk_base.tools import dingtalk_api


class HrLeavesListTran(models.TransientModel):
    _name = 'hr.leaves.list.tran'
    _description = "获取请假列表"

    user_ids = fields.Many2many('hr.employee', string=u'待查用户', required=True)
    start_time = fields.Date(string=u'开始时间', required=True)
    end_time = fields.Date(string=u'结束时间', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    def get_leaves_list(self):
        """
        查询请假状态
        :return:
        """
        self.ensure_one()
        din_client = dingtalk_api.get_client()
        offset = 0
        size = 20
        user_list = list()
        for emp in self.user_ids:
            if emp.ding_id:
                user_list.append(emp.ding_id)
        user_list = dingtalk_api.list_cut(user_list, 100)
        for u in user_list:
            user_str = ",".join(u)
            while True:
                try:
                    result = din_client.attendance.getleavestatus(
                        user_str, self.start_time, self.end_time, offset=offset, size=size)
                    logging.info(">>>查询请假状态返回结果%s", result)
                    leave_status = result['leave_status']
                    if leave_status:
                        leave_list = list()
                        for leave in leave_status.get('leave_status_v_o'):
                            leave_data = {
                                'start_time_stamp': leave['start_time'],
                                'end_time_stamp': leave['end_time'],
                                'duration_unit': leave['duration_unit'],
                                'duration_percent': leave['duration_percent'] / 100,
                                'end_time': dingtalk_api.timestamp_to_local_date(leave['end_time']),
                                'start_time': dingtalk_api.timestamp_to_local_date(leave['start_time']),
                            }
                            employee = self.env['hr.employee'].search([('ding_id', '=', leave['userid'])], limit=1)
                            leave_data.update({
                                'user_id': employee.id if employee else False,
                                'din_jobnumber': employee.din_jobnumber if employee else False,
                            })
                            leave_list.append(leave_data)
                            # 删除已存在的请假记录
                            domain = [('start_time_stamp', '=', leave['start_time']), ('user_id', '=', employee.id), ('end_time_stamp', '=', leave['end_time'])]
                            self.env['hr.leaves.list'].search(domain).unlink()
                        # 批量存储记录
                        self.env['hr.leaves.list'].create(leave_list)
                    if not result['has_more']:
                        break
                    else:
                        offset += size
                except Exception as e:
                    raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            employees = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(employees) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.user_ids = [(6, 0, employees.ids)]
