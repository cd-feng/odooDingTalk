# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# 拓展员工
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    din_group_id = fields.Many2one(comodel_name='dindin.simple.groups', string=u'考勤组')


class DinDinSimpleGroups(models.Model):
    _name = 'dindin.simple.groups'
    _description = '考勤组'

    name = fields.Char(string='名称')
    group_id = fields.Char(string='钉钉考勤组ID')

    s_type = fields.Selection(string=u'考勤类型',
                              selection=[('FIXED', '固定排班'), ('TURN', '轮班排班'), ('NONE', '无班次')], default='NONE')
    member_count = fields.Integer(string=u'成员人数')
    manager_list = fields.Many2many(comodel_name='hr.employee', relation='dindin_simple_group_hr_emp_rel',
                                    column1='group_id', column2='emp_id', string=u'负责人')
    dept_name_list = fields.Many2many(comodel_name='hr.department', relation='dindin_simple_group_hr_dept_rel',
                                      column1='group_id', column2='dept_id', string=u'关联部门')
    emp_ids = fields.One2many(comodel_name='hr.employee', inverse_name='din_group_id', string=u'成员列表')

    @api.model
    def get_simple_groups(self):
        """
        获取考勤组
        :return:
        """
        logging.info(">>>获取考勤组...")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'attendance_getsimplegroups')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'offset': 0,
            'size': 10,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=15)
            result = json.loads(result.text)
            logging.info(result)
            if result.get('errcode') == 0:
                result = result.get('result')
                for group in result.get('groups'):
                    data = {
                        'group_id': group.get('group_id'),
                        'name': group.get('group_name'),
                        's_type': group.get('type'),
                        'member_count': int(group.get('member_count')),
                    }
                    manager_ids = list()
                    if group.get('manager_list'):
                        for emp in group.get('manager_list'):
                            emp_res = self.env['hr.employee'].sudo().search([('din_id', '=', emp)])
                            if emp_res:
                                manager_ids.append(emp_res.id)
                    data.update({'manager_list': [(6, 0, manager_ids)]})
                    self_group = self.env['dindin.simple.groups'].search([('group_id', '=', group.get('group_id'))])
                    if self_group:
                        self_group.sudo().write(data)
                    else:
                        self.env['dindin.simple.groups'].sudo().create(data)
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
        emps = self.env['hr.employee'].sudo().search([('din_id', '!=', '')])
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'a_getusergroup')]).value
        headers = {'Content-Type': 'application/json'}
        for emp in emps:
            data = {
                'userid': emp.din_id
            }
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=10)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    res = result.get('result')
                    groups = self.env['dindin.simple.groups'].sudo().search([('group_id', '=', res.get('group_id'))])
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


