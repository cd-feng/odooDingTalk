# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class EmployeeRosterSynchronous(models.TransientModel):
    _name = 'dingtalk.employee.roster.synchronous'
    _description = "智能人事花名册同步"

    company_ids = fields.Many2many("res.company", string="同步的公司", required=True, default=lambda self: self.env.ref('base.main_company'))

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
                            'emp_id': emp_data[rec['userid']] if rec['userid'] in emp_data else False,
                            'ding_userid': rec['userid'],
                            'company_id': company_id
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            # 获取部门（可能会多个）
                            if fie['field_code'][6:] == 'deptIds' and 'value' in fie:
                                dept_ding_ids = fie['value'].split('|')
                                domain = [('company_id', '=', company_id), ('ding_id', 'in', dept_ding_ids)]
                                departments = self.env['hr.department'].sudo().search(domain)
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId' and 'value' in fie:
                                domain = [('company_id', '=', company_id), ('ding_id', '=', fie['value'])]
                                dept = self.env['hr.department'].sudo().search(domain, limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position' and 'label' in fie:
                                domain = [('company_id', '=', company_id), ('name', '=', fie['label'])]
                                hr_job = self.env['hr.job'].sudo().search(domain, limit=1)
                                if not hr_job and fie['label']:
                                    hr_job = self.env['hr.job'].sudo().create({'name': fie['label'], 'company_id': company_id})
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
        employees = self.env['hr.employee'].sudo().search([('ding_id', '!=', ''), ('company_id', '=', company_id)])
        # result = self.env['hr.employee'].sudo().search_read([('ding_id', '!=', ''), ('company_id', '=', company_id)], ['ding_id', 'id'])
        emp_data = dict()
        for emp in employees:
            emp_data.update({
                emp.ding_id: emp.id,
            })
        return emp_data



