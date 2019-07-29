# -*- coding: utf-8 -*-
import logging
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# 拓展员工
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    din_group_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'考勤组', index=True)


class DingDingSimpleGroups(models.Model):
    _name = 'dingding.simple.groups'
    _rec_name = 'name'
    _description = '考勤组'

    ATTENDANCETYPE = [
        ('FIXED', '固定排班'),
        ('TURN', '轮班排班'),
        ('NONE', '无班次')
    ]

    name = fields.Char(string='名称', index=True)
    group_id = fields.Char(string='钉钉考勤组ID', index=True)
    s_type = fields.Selection(string=u'考勤类型', selection=ATTENDANCETYPE, default='NONE')
    member_count = fields.Integer(string=u'成员人数')
    manager_list = fields.Many2many('hr.employee', string=u'负责人', index=True)
    dept_name_list = fields.Many2many('hr.department', string=u'关联部门')
    classes_list = fields.Char(string='班次时间展示')
    emp_ids = fields.One2many(comodel_name='hr.employee', inverse_name='din_group_id', string=u'成员列表')
    list_ids = fields.One2many(comodel_name='dingding.simple.groups.list', inverse_name='simple_id', string=u'班次列表')

    @api.model
    def get_simple_groups(self):
        """
        获取考勤组
        :return:
        """
        logging.info(">>>获取考勤组...")
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('attendance_getsimplegroups')
        data = {'offset': 0, 'size': 10}
        try:
            result = self.env['dingding.api.tools'].send_post_request(url, token, data)
            if result.get('errcode') == 0:
                result = result.get('result')
                for group in result.get('groups'):
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
                        for selected in group['selected_class']:
                            setting = selected['setting']
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
                            if 'rest_begin_time' in  setting:
                                rest_begin_time = setting['rest_begin_time']
                                b_data.update({'rest_begin_time': rest_begin_time['check_time']})
                            if 'rest_end_time' in setting:
                                rest_end_time = setting['rest_end_time']
                                b_data.update({'rest_end_time': rest_end_time['check_time']})
                            # 打卡时间段
                            time_list = list()
                            for sections in selected['sections']:
                                for time in sections['times']:
                                    time_list.append((0, 0, {
                                        'across': time['across'],
                                        'check_time': time['check_time'],
                                        'check_type': time['check_type'],
                                    }))
                            b_data.update({'time_ids': time_list})
                            list_ids.append((0, 0, b_data))
                    data.update({'list_ids': list_ids})
                    self_group = self.env['dingding.simple.groups'].search([('group_id', '=', group.get('group_id'))])
                    if self_group:
                        for group_list in self_group.list_ids:
                            group_list.sudo().unlink()
                        self_group.sudo().write(data)
                    else:
                        self.env['dingding.simple.groups'].sudo().create(data)
            else:
                raise UserError('获取考勤组失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取考勤组结束...")
        return True

    @api.model
    def get_sim_emps(self):
        """
        获取考勤组成员
        :return:
        """
        self.get_simple_groups()  # 获取考勤组成员前先更新考勤组
        emps = self.env['hr.employee'].sudo().search([('ding_id', '!=', '')])
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('a_getusergroup')
        for emp in emps:
            data = {'userid': emp.ding_id}
            try:
                result = self.env['dingding.api.tools'].send_post_request(url, token, data, 1)
                if result.get('errcode') == 0:
                    res = result.get('result')
                    groups = self.env['dingding.simple.groups'].sudo().search([('group_id', '=', res.get('group_id'))])
                    if groups:
                        self._cr.execute(
                            """UPDATE hr_employee SET din_group_id = {} WHERE id = {}""".format(groups[0].id, emp.id))
                    else:
                        pass
                else:
                    return {'state': False, 'msg': '请求失败,原因为:{}'.format(result.get('errmsg'))}
            except ReadTimeout:
                return {'state': False, 'msg': '网络连接超时!'}
        return {'state': True, 'msg': '执行成功!'}


class DingDingSimpleGroupsList(models.Model):
    _description = "班次列表"
    _name = 'dingding.simple.groups.list'
    _rec_name = 'class_name'

    simple_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'考勤组', index=True)
    class_name = fields.Char(string='考勤班次名称', index=True)
    class_id = fields.Char(string='考勤班次Id', index=True)

    # setting
    class_setting_id = fields.Char(string='考勤组班次id')
    rest_begin_time = fields.Char(string='休息开始时间', help="只有一个时间段的班次有")
    check_time = fields.Char(string='开始时间', help="开始时间")
    permit_late_minutes = fields.Char(string='允许迟到时长(分钟)', help="允许迟到时长，单位分钟")
    work_time_minutes = fields.Char(string='工作时长', help="单位分钟，-1表示关闭该功能")
    rest_end_time = fields.Char(string='休息结束时间', help="只有一个时间段的班次有")
    end_time = fields.Char(string='结束时间', help="结束时间")
    absenteeism_late_minutes = fields.Char(string='旷工迟到分钟', help="旷工迟到时长，单位分钟")
    serious_late_minutes = fields.Char(string='严重迟到分钟', help="严重迟到时长，单位分钟")
    is_off_duty_free_check = fields.Selection(string=u'强制打卡', selection=[('Y', '下班不强制打卡'), ('N', '下班强制打卡')])
    
    # sections
    time_ids = fields.One2many(comodel_name='dingding.simple.groups.list.time', inverse_name='list_id', string=u'打卡时间段')


class DingDingSimpleGroupsListTime(models.Model):
    _description = "班次打卡时间段"
    _name = 'dingding.simple.groups.list.time'
    _rec_name = 'list_id'

    list_id = fields.Many2one(comodel_name='dingding.simple.groups.list', string=u'班次', index=True)
    across = fields.Char(string=u'打卡时间跨度')
    check_time = fields.Datetime(string=u'打卡时间')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])

