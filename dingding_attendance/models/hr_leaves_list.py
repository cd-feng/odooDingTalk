# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrLeavesList(models.Model):
    _name = "hr.leaves.list"
    _rec_name = 'user_id'
    _description = "请假列表"

    user_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    duration_unit = fields.Selection(string=u'请假单位', selection=[('percent_day', '天'), ('percent_hour', '小时')])
    duration_percent = fields.Integer(string=u'请假时长')
    start_time = fields.Datetime(string=u'请假开始时间')
    end_time = fields.Datetime(string=u'请假结束时间')
    start_time_stamp = fields.Char(string='开始时间戳字符串')
    end_time_stamp = fields.Char(string='结束时间戳字符串')


class HrLeavesListTran(models.TransientModel):
    _name = 'hr.leaves.list.tran'
    _description = "获取请假列表"

    user_ids = fields.Many2many('hr.employee', string=u'待查用户', required=True)
    start_time = fields.Datetime(string=u'开始时间', required=True)
    end_time = fields.Datetime(string=u'结束时间', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.multi
    def get_leaves_list(self):
        """
        查询请假状态
        :return:
        """
        self.ensure_one()
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('a_getleavestatus')
        offset = 0
        size = 20
        start_time = str(self.env['dingding.api.tools'].datetime_to_stamp(self.start_time))[:12]
        end_time = str(self.env['dingding.api.tools'].datetime_to_stamp(self.end_time))[:12]
        user_str = ''
        for user in self.user_ids:
            if user_str == '':
                user_str = user_str + "{}".format(user.ding_id)
            else:
                user_str = user_str + ",{}".format(user.ding_id)
        data = {'userid_list': user_str, 'start_time': start_time, 'end_time': end_time}
        while True:
            data.update({'offset': offset, 'size': size})
            result = self.env['dingding.api.tools'].send_post_request(url, token, data)
            if result.get('errcode') == 0:
                res_result = result['result']
                for leave in res_result['leave_status']:
                    leave_data = {
                        'start_time_stamp': leave['start_time'],
                        'end_time_stamp': leave['end_time'],
                        'duration_unit': leave['duration_unit'],
                        'duration_percent': leave['duration_percent'],
                        'end_time': self.env['dingding.api.tools'].get_time_stamp(leave['end_time']),
                        'start_time': self.env['dingding.api.tools'].get_time_stamp(leave['start_time']),
                    }
                    employee = self.env['hr.employee'].search([('end_time', '=', leave['userid'])], limit=1)
                    leave_data.update({
                        'user_id': employee.id if employee else False,
                    })
                    domain = [('start_time_stamp', '=', leave['start_time']), ('user_id', '=', employee.id), ('end_time_stamp', '=', leave['end_time'])]
                    hr_leaves = self.env['hr.leaves.list'].search(domain)
                    if not hr_leaves:
                        self.env['hr.leaves.list'].create(leave_data)
                    else:
                        hr_leaves.write(leave_data)
                if not res_result['has_more']:
                    break
                else:
                    offset += 1
            else:
                raise UserError("查询请假状态失败: {}".format(result['errmsg']))
        action = self.env.ref('dingding_attendance.hr_leaves_list_action')
        action_dict = action.read()[0]
        return action_dict










    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            employees = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(employees) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.user_ids = [(6, 0, employees.ids)]