# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  License(GNU)
###################################################################################
import logging
import time
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EmployeeRosterSynchronous(models.TransientModel):
    _name = 'dingding.employee.roster.synchronous'
    _description = "智能人事花名册同步"

    synchronous_onjob = fields.Boolean(string=u'同步在职花名册', default=True)
    synchronous_dimission = fields.Boolean(string=u'同步离职花名册', default=True)
    synchronous_dimission_info = fields.Boolean(string=u'同步离职信息', default=True)

    @api.multi
    def start_synchronous_data(self):
        """
        花名册同步
        :return:
        """
        for res in self:
            try:
                if res.synchronous_onjob:
                    self.get_onjob_list()
                if res.synchronous_dimission:
                    self.get_dimission_list()
                if res.synchronous_dimission_info:
                    self.get_dimission_info()
            except Exception as e:
                raise UserError(e)

    @api.model
    def get_onjob_userid_list(self):
        """
        智能人事查询公司在职员工userid列表
        智能人事业务，提供企业/ISV按在职状态分页查询公司在职员工id列表
        :param status_list: 在职员工子状态筛选。2，试用期；3，正式；5，待离职；-1，无状态
        :param offset: 分页起始值，默认0开始
        :param size: 分页大小，最大50
        """
        din_client = self.env['dingding.api.tools'].get_client()
        onjob_list = list()
        status_arr = ['2', '3', '5', '-1']
        offset = 0
        size = 50
        while True:
            try:
                result = din_client.employeerm.queryonjob(status_list=status_arr, offset=offset, size=size)
                # logging.info(">>>获取在职员工列表返回结果%s", result)
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

    @api.multi
    def get_onjob_list(self):
        """
        获取钉钉在职员工花名册
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉在职员工花名册start")
        emp_data = self.get_employee_to_dict()
        onjob_userid_list = self.get_onjob_userid_list()
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(onjob_userid_list, 20)
        for u in user_list:
            try:
                result = din_client.employeerm.list(u, field_filter_list=())
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
                                for depa in fie['value'].split('|'):
                                    dept_ding_ids.append(depa)
                                departments = self.env['hr.department'].sudo().search(
                                    [('ding_id', 'in', dept_ding_ids)])
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId' and 'value' in fie:
                                dept = self.env['hr.department'].sudo().search(
                                    [('ding_id', '=', fie['value'])], limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position' and 'label' in fie:
                                hr_job = self.env['hr.job'].sudo().search([('name', '=', fie['label'])])
                                if not hr_job and fie['label']:
                                    hr_job = self.env['hr.job'].sudo().create({'name': fie['label']})
                                roster_data.update({'position': hr_job.id})
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else ''
                                })
                        roster = self.env['dingding.employee.roster'].sudo().search([('ding_userid', '=', rec['userid'])])
                        if roster:
                            roster.sudo().write(roster_data)
                        else:
                            self.env['dingding.employee.roster'].sudo().create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        logging.info(">>>获取钉钉在职员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_employee_roster_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def get_dimission_userid_list(self):
        """
        获取离职员工userid列表
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        dimission_list = list()
        offset = 0
        size = 50
        while True:
            try:
                result = din_client.employeerm.querydimission(offset=offset, size=size)
                # logging.info(">>>获取离职员工列表返回结果%s", result)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    dimission_list.extend(result_list)
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                    else:
                        break
                else:
                    break
            except Exception as e:
                raise UserError(e)
        return dimission_list

    @api.multi
    def get_dimission_list(self):
        """
        获取钉钉离职员工花名册
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉离职员工花名册start")
        emp_data = self.get_employee_to_dict()
        dimission_userid_list = self.get_dimission_userid_list()
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(dimission_userid_list, 20)
        for u in user_list:
            try:
                result = din_client.employeerm.list(u, field_filter_list=())
                # logging.info(">>>获取花名册返回结果%s", result)
                if result.get('emp_field_info_v_o'):
                    for rec in result.get('emp_field_info_v_o'):
                        # logging.info(">>>当前离职员工%s", rec)
                        roster_data = {
                            'emp_id': emp_data[rec['userid']] if rec['userid'] in emp_data else False,
                            'ding_userid': rec['userid']
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            # 获取部门（可能会多个）
                            if fie['field_code'][6:] == 'deptIds' and 'value' in fie:
                                dept_ding_ids = list()
                                for depa in fie['value'].split('|'):
                                    dept_ding_ids.append(depa)
                                departments = self.env['hr.department'].sudo().search(
                                    [('ding_id', 'in', dept_ding_ids)])
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId' and 'value' in fie:
                                dept = self.env['hr.department'].sudo().search(
                                    [('ding_id', '=', fie['value'])], limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position' and 'label' in fie:
                                if fie['label']:
                                    hr_job = self.env['hr.job'].sudo().search([('name', '=', fie['label'])])
                                    if not hr_job and fie['label']:
                                        hr_job = self.env['hr.job'].sudo().create({'name': fie['label']})
                                roster_data.update({
                                    'position': hr_job.id
                                })
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else ''
                                })
                        roster = self.env['dingding.employee.roster'].sudo().search(
                            [('ding_userid', '=', rec['userid'])])
                        if roster:
                            roster.sudo().write(roster_data)
                        else:
                            self.env['dingding.employee.roster'].sudo().create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        logging.info(">>>获取钉钉离职员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_employee_roster_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def get_dimission_info(self):
        """
        获取全部员工离职信息
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉离职员工信息start")
        # emp_data = self.get_employee_to_dict()
        dimission_userid_list = self.get_dimission_userid_list()
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(dimission_userid_list, 50)
        for u in user_list:
            try:
                result = din_client.employeerm.listdimission(userid_list=u)
                # logging.info(">>>批量获取员工离职信息返回结果%s", result)
                if result.get('emp_dimission_info_vo'):
                    for res in result.get('emp_dimission_info_vo'):
                        data = {
                            'last_work_day': self.stamp_to_time(res.get('last_work_day')),
                            'reason_memo': res.get('reason_memo'),
                            'reason_type': str(res.get('reason_type')) if res.get('reason_type') else '9',
                            'pre_status': str(res.get('pre_status'))
                        }
                        if res.get('handover_userid'):
                            handover_userid = self.env['dingding.employee.roster'].search(
                                [('ding_userid', '=', res.get('handover_userid'))])
                            data.update({'handover_userid': handover_userid.id})
                        emp = self.env['dingding.employee.roster'].search(
                            [('ding_userid', '=', res.get('userid'))])
                        if emp:
                            emp.write(data)
                        # else:
                        #     self.env['dingding.hrm.dimission.list'].create(data)

            except Exception as e:
                raise UserError(e)
        logging.info(">>>获取获取离职员工信息end")

    def get_employee_to_dict(self):
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

    def stamp_to_time(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000)
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
