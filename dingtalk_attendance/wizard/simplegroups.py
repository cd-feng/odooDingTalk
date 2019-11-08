# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class GetDingTalkSimpleGroupsTran(models.TransientModel):
    _name = 'dingtalk.simple.groups.tran'
    _description = "获取考勤组"

    def get_simple_groups(self):
        """
        获取考勤组
        :return:
        """
        client = dingtalk_api.get_client()
        offset = 0
        size = 10
        while True:
            try:
                result = client.attendance.getsimplegroups(offset, size)
                _logger.info(">>>获取考勤组列表返回结果%s", result)
                if result.get('ding_open_errcode') == 0:
                    result = result.get('result')
                    groups = result.get('groups')
                    at_group_for_top_vo = []
                    if groups:
                        at_group_for_top_vo = result.get('groups').get('at_group_for_top_vo')
                    if at_group_for_top_vo:
                        for group in at_group_for_top_vo:
                            # -----读取考勤信息
                            data = {
                                'group_id': group.get('group_id'),
                                'name': group.get('group_name'),
                                's_type': group.get('type'),
                                'classes_list': group.get('classes_list'),
                                'member_count': int(group.get('member_count')),
                            }
                            manager_ids = list()
                            if group.get('manager_list'):
                                for emp in group.get('manager_list'):
                                    emp_res = self.env['hr.employee'].sudo().search([('ding_id', '=', emp)])
                                    if emp_res:
                                        manager_ids.append(emp_res.id)
                            data.update({'manager_list': [(6, 0, manager_ids)]})
                            # -----读取班次
                            list_ids = list()
                            if 'selected_class' in group:
                                selected_class = group['selected_class']
                                if 'at_class_vo' in selected_class:
                                    for selected in selected_class.get('at_class_vo'):
                                        setting = selected.get('setting')
                                        b_data = {
                                            'class_name': selected['class_name'],
                                            'class_id': selected['class_id'],
                                            'serious_late_minutes': setting['serious_late_minutes'],
                                            'class_setting_id': setting['class_setting_id'],
                                            'work_time_minutes': setting['work_time_minutes'],
                                            'permit_late_minutes': setting['permit_late_minutes'],
                                            'absenteeism_late_minutes': setting['absenteeism_late_minutes'],
                                            'is_off_duty_free_check': setting['is_off_duty_free_check'],
                                        }
                                        if 'rest_begin_time' in setting:
                                            rest_begin_time = setting['rest_begin_time']
                                            b_data.update({'rest_begin_time': rest_begin_time['check_time']})
                                        if 'rest_end_time' in setting:
                                            rest_end_time = setting['rest_end_time']
                                            b_data.update({'rest_end_time': rest_end_time['check_time']})
                                        # 打卡时间段
                                        time_list = list()
                                        for sections in selected['sections']['at_section_vo']:
                                            for time in sections['times']['at_time_vo']:
                                                time_list.append((0, 0, {
                                                    'across': time['across'],
                                                    'check_time': time['check_time'],
                                                    'check_type': time['check_type'],
                                                }))
                                        b_data.update({'time_ids': time_list})
                                        list_ids.append((0, 0, b_data))
                            data.update({'list_ids': list_ids})
                            self_group = self.env['dingtalk.simple.groups'].search([('group_id', '=', group.get('group_id'))])
                            if self_group:
                                for group_list in self_group.list_ids:
                                    group_list.sudo().unlink()
                                self_group.sudo().write(data)
                            else:
                                self.env['dingtalk.simple.groups'].sudo().create(data)
                    if result.get('has_more'):
                        offset = offset + 1
                        size = 10
                    else:
                        break
            except Exception as e:
                raise UserError(e)


class GetDingTalkSimpleGroupsUsersTran(models.TransientModel):
    _name = 'dingtalk.simple.groups.users.tran'
    _description = "获取考勤组成员"

    def get_sim_emps(self):
        """
        获取考勤组成员
        :return:
        """
        groups = self.env['dingtalk.simple.groups'].search([])
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if not emp or not emp.ding_id:
            raise UserError("请使用钉钉员工登录系统后进行操作，或则将当前登录用户关联一个钉钉员工!")
        client = dingtalk_api.get_client()
        url = "topapi/attendance/group/memberusers/list"
        for group in groups:
            while True:
                cursor = 1
                try:
                    result = client.post(url, {
                        'op_user_id': emp.ding_id,
                        'cursor': cursor,
                        'group_id': group.group_id,
                    })
                except Exception as e:
                    raise UserError(e)
                if result.get('errcode') == 0:
                    result = result.get('result')
                    if result.get('result'):
                        emps = self.env['hr.employee'].sudo().search([('ding_id', 'in', result.get('result'))])
                        group.write({'emp_ids': [(6, 0, emps.ids)]})
                        self._cr.commit()
                    if result.get('has_more'):
                        cursor = result.get('cursor')
                    else:
                        break
        return {'type': 'ir.actions.act_window_close'}
