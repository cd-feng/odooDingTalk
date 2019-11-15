# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  License(GNU)
###################################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class EmployeeRosterSynchronous(models.TransientModel):
    _name = 'dingtalk.employee.roster.synchronous'
    _description = "智能人事花名册同步"

    def start_synchronous_data(self):
        """
        花名册同步
        :return:
        """
        self.ensure_one()
        _logger.info(">>>获取钉钉在职员工花名册...")
        client = dingtalk_api.get_client()
        emp_data = self._get_employee_to_dict()
        userid_list = self._get_onjob_userid_list(client)
        self._create_employee_roster(client, dingtalk_api.list_cut(userid_list, 20), emp_data)
        return {'type': 'ir.actions.act_window_close'}

    def _get_onjob_userid_list(self, client):
        """
        智能人事查询公司在职员工userid列表
        智能人事业务，提供企业/ISV按在职状态分页查询公司在职员工id列表
        :param client: 钉钉客户端
        :param status_list: 在职员工子状态筛选。2，试用期；3，正式；5，待离职；-1，无状态
        :param offset: 分页起始值，默认0开始
        :param size: 分页大小，最大50
        """
        onjob_list = list()
        status_arr = ['2', '3', '5', '-1']
        offset = 0
        size = 50
        while True:
            try:
                result = client.employeerm.queryonjob(status_list=status_arr, offset=offset, size=size)
                # _logger.info(">>>获取在职员工列表返回结果%s", result)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    onjob_list.extend(result_list)
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                    else:
                        break
                else:
                    break
            except Exception as e:
                raise UserError(e)
        return onjob_list

    def _create_employee_roster(self, client, user_list, emp_data):
        """
        获取钉钉在职员工花名册
        :return:
        """
        for user in user_list:
            try:
                result = client.employeerm.list(user, field_filter_list=())
                if result.get('emp_field_info_v_o'):
                    for rec in result.get('emp_field_info_v_o'):
                        roster_data = {
                            'emp_id': emp_data[rec['userid']] if rec['userid'] in emp_data else False,
                            'ding_userid': rec['userid']
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            # 获取部门（可能会多个）
                            if fie['field_code'][6:] == 'deptIds' and 'value' in fie:
                                dept_ding_ids = list()
                                for dept in fie['value'].split('|'):
                                    dept_ding_ids.append(dept)
                                departments = self.env['hr.department'].sudo().search([('ding_id', 'in', dept_ding_ids)])
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId' and 'value' in fie:
                                dept = self.env['hr.department'].sudo().search([('ding_id', '=', fie['value'])], limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position' and 'label' in fie:
                                hr_job = self.env['hr.job'].sudo().search([('name', '=', fie['label'])], limit=1)
                                if not hr_job and fie['label']:
                                    hr_job = self.env['hr.job'].sudo().create({'name': fie['label']})
                                roster_data.update({'position': hr_job.id or False})
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else False
                                })
                        roster = self.env['dingtalk.employee.roster'].sudo().search([('ding_userid', '=', rec['userid'])])
                        if roster:
                            roster.sudo().write(roster_data)
                        else:
                            self.env['dingtalk.employee.roster'].sudo().create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        return

    def _get_employee_to_dict(self):
        """
        将员工封装为字典并返回
        :return:
        """
        employees = self.env['hr.employee'].sudo().search([('ding_id', '!=', '')])
        emp_data = dict()
        for emp in employees:
            emp_data.update({
                emp.ding_id: emp.id,
            })
        return emp_data



