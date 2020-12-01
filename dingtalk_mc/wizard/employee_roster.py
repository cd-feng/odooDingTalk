# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class EmployeeRosterSynchronous(models.TransientModel):
    _name = 'dingtalk.employee.roster.synchronous'
    _description = "智能人事花名册同步"

    company_ids = fields.Many2many("res.company", string="同步的公司", required=True, default=lambda self: [(6, 0, [self.env.company.id])])

    def start_synchronous_data(self):
        """
        花名册同步
        :return:
        """
        self.ensure_one()
        for company in self.company_ids:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            emp_data = self.get_employee_to_dict(company.id)
            userid_list = self.get_onjob_userid_list(client)
            self.create_employee_roster(client, dt.list_cut(userid_list, 20), emp_data, company.id)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def get_onjob_userid_list(self, client):
        """
        智能人事查询公司在职员工userid列表
        智能人事业务，提供企业/ISV按在职状态分页查询公司在职员工id列表
        :param client: 钉钉客户端
        """
        onjob_list = list()
        status_arr = ['2', '3', '5', '-1']  # 在职员工子状态筛选。2，试用期；3，正式；5，待离职；-1，无状态
        offset = 0     # 分页起始值，默认0开始
        size = 50      # 分页大小，最大50
        while True:
            try:
                result = client.employeerm.queryonjob(status_list=status_arr, offset=offset, size=size)
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

    def create_employee_roster(self, client, user_list, emp_data, company_id):
        """
        获取钉钉在职员工花名册
        :param client:
        :param user_list:
        :param emp_data:
        :param company_id:
        :return:
        """
        for user in user_list:
            try:
                result = client.employeerm.list(user, field_filter_list=())
                if result.get('emp_field_info_v_o'):
                    for rec in result.get('emp_field_info_v_o'):
                        roster_data = {
                            'emp_id': emp_data.get(rec['userid']),
                            'ding_userid': rec['userid'],
                            'company_id': company_id
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            if len(fie['field_code']) > 30:
                                continue
                            # 获取部门（可能会多个）
                            elif fie['field_code'][6:] == 'deptIds':
                                if 'value' not in fie:
                                    continue
                                dept_ding_ids = fie['value'].split('|')
                                domain = [('company_id', '=', company_id), ('ding_id', 'in', dept_ding_ids)]
                                departments = self.env['hr.department'].with_user(SUPERUSER_ID).search(domain)
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId':
                                if 'value' not in fie:
                                    continue
                                domain = [('company_id', '=', company_id), ('ding_id', '=', fie['value'])]
                                dept = self.env['hr.department'].with_user(SUPERUSER_ID).search(domain, limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position':
                                if 'label' not in fie:
                                    continue
                                domain = [('company_id', '=', company_id), ('name', '=', fie['label'])]
                                hr_job = self.env['hr.job'].with_user(SUPERUSER_ID).search(domain, limit=1)
                                if not hr_job and fie['label']:
                                    hr_job = self.env['hr.job'].with_user(SUPERUSER_ID).create({'name': fie['label'], 'company_id': company_id})
                                roster_data.update({'position': hr_job.id or False})
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else False
                                })
                        domain = [('company_id', '=', company_id), ('ding_userid', '=', rec['userid'])]
                        roster = self.env['dingtalk.employee.roster'].search(domain)
                        if roster:
                            roster.write(roster_data)
                        else:
                            self.env['dingtalk.employee.roster'].create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        return

    @api.model
    def get_employee_to_dict(self, company_id):
        """
        将员工封装为字典并返回
        :param: company_id 公司id
        :return:
        """
        employees = self.env['hr.employee'].with_user(SUPERUSER_ID).search([('ding_id', '!=', ''), ('company_id', '=', company_id)])
        emp_data = dict()
        for emp in employees:
            emp_data.update({
                emp.ding_id: emp.id,
            })
        return emp_data

    @api.model
    def sync_to_employees(self):
        """
        将部分字段同步到系统员工
        :return:
        """
        for res in self.env['dingtalk.employee.roster'].search([]):
            if res.emp_id:
                if res.sexType == '男':
                    gender = 'male'
                elif res.sexType == '女':
                    gender = 'female'
                else:
                    gender = 'other'
                res.emp_id.write({
                    'identification_id': res.certNo,
                    'work_location': res.workPlace,
                    'phone': res.mobile,
                    'study_school': res.graduateSchool,
                    'birthday': res.birthTime,
                    'place_of_birth': res.certAddress,
                    'gender': gender,
                    'job_id': res.position.id
                })


class SynchronizeLeavingEmployees(models.TransientModel):
    _name = 'dingtalk.synchronize.leaving.employees'
    _description = "同步离职员工信息"
    
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company, required=True)

    def on_synchronous(self):
        """
        开始同步离职员工信息
        :return:
        """
        self.ensure_one()
        client = dt.get_client(self, dt.get_dingtalk_config(self, self.company_id))
        leaving_user_list = self.get_leaving_user_list(client, self.company_id)
        self.get_dimission_list(client, leaving_user_list, self.company_id)
        return {'type': 'ir.actions.act_window_close'}

    def get_all_employee_dict(self, company_id):
        """
        返回员工钉钉iddict
        :return:
        """
        emp_dict = {}
        domain = [('ding_id', '!=', False), ('company_id', '=', company_id.id)]
        for emp in self.env['hr.employee'].search(domain):
            emp_dict[emp.ding_id] = emp.id
        return emp_dict

    def get_leaving_user_list(self, client, company_id):
        # 获取离职员工列表
        offset = 0
        size = 50
        leaving_user_list = []
        new_leaving_user_list = []
        try:
            while True:
                req_result = client.post('topapi/smartwork/hrm/employee/querydimission', {
                    'offset': offset,
                    'size': size,
                })
                if req_result.get('errcode') != 0:
                    raise UserError(req_result.get('errmsg'))
                result = req_result.get('result')
                leaving_user_list.extend(result.get('data_list'))
                if not result.get('next_cursor'):
                    break
                offset = result.get('next_cursor')
        except Exception as e:
            raise UserError("获取失败！原因:{}".format(e))
        emp_ding_ids = []
        domain = [('ding_id', '!=', False), ('company_id', '=', company_id.id)]
        for emp in self.env['hr.employee'].search(domain):
            emp_ding_ids.append(emp.ding_id)
        # 去掉中不在系统的员工
        for leaving_user in leaving_user_list:
            if leaving_user in emp_ding_ids:
                new_leaving_user_list.append(leaving_user)
        return new_leaving_user_list

    def get_dimission_list(self, client, leaving_user_list, company_id):
        """
        获取离职员工详情
        :return:
        """
        leaving_user_list = dt.list_cut(leaving_user_list, 50)
        emp_dict = self.get_all_employee_dict(company_id)
        for leaving_user in leaving_user_list:
            userid_list = str()
            for leaving_id in leaving_user:
                if userid_list:
                    userid_list = "{},{}".format(userid_list, leaving_id)
                else:
                    userid_list = leaving_id
            try:
                req_result = client.post('topapi/smartwork/hrm/employee/listdimission', {
                    'userid_list': userid_list,
                })
                if req_result.get('errcode') != 0:
                    raise UserError(req_result.get('errmsg'))
                result = req_result.get('result')
                for res in result:
                    userid = res.get('userid')
                    try:
                        emp_id = emp_dict[userid]
                    except KeyError:
                        continue
                    data = {
                        'emp_id': emp_id,
                        'reason_memo': res.get('reason_memo'),
                        'handover_userid': emp_dict.get(res.get('handover_userid')),
                        'main_dept_name': res.get('main_dept_name'),
                        'main_dept_id': res.get('main_dept_id'),
                    }
                    if res.get('last_work_day'):
                        data['last_work_day'] = dt.get_time_stamp(res.get('last_work_day'))
                    if res.get('reason_type'):
                        data['reason_type'] = str(res.get('reason_type'))
                    if res.get('pre_status'):
                        data['pre_status'] = str(res.get('pre_status'))
                    if res.get('status'):
                        data['status'] = str(res.get('status'))
                    e_roster = self.env['dingtalk.leaving.employee.roster'].search([('emp_id', '=', emp_id)])
                    if e_roster:
                        e_roster.write(data)
                    else:
                        self.env['dingtalk.leaving.employee.roster'].create(data)
            except Exception as e:
                raise UserError("获取失败！原因:{}".format(e))
