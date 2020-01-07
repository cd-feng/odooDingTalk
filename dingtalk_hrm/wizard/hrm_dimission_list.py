# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class GetDingTalkHrmDimissionList(models.TransientModel):
    _name = 'dingtalk.get.hrm.dimission.list'
    _description = '获取离职员工信息'

    emp_ids = fields.Many2many('hr.employee', string='员工', required=True)
    is_all_emp = fields.Boolean(string='全部离职员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search(
                [('ding_id', '!=', ''), ('work_status', '=', '3')])
            self.emp_ids = [(6, 0, emps.ids)]
        else:
            self.emp_ids = False

    def get_hrm_dimission_list(self):
        """
        批量获取员工离职信息
        """
        client = dingtalk_api.get_client(self)
        dimission_list = self._get_dimission_userid_list(client)
        user_list = dingtalk_api.list_cut(dimission_list, 20)
        for user in user_list:
            try:
                result = client.employeerm.listdimission(user)
                if result.get('emp_dimission_info_vo'):
                    for res in result.get('emp_dimission_info_vo'):
                        if res.get('main_dept_id'):
                            main_dept = self.env['hr.department'].search([('ding_id', '=', res.get('main_dept_id'))], limit=1)
                        dept_list = list()
                        if res.get('dept_list'):
                            for depti in res['dept_list']['emp_dept_v_o']:
                                hr_dept = self.env['hr.department'].search([('ding_id', '=', depti.get('dept_id'))])
                                if hr_dept:
                                    dept_list.append(hr_dept.id)
                        data = {
                            'ding_id': res.get('userid'),
                            'last_work_day': dingtalk_api.timestamp_to_local_date(self, res.get('last_work_day')),
                            'department_ids': [(6, 0, dept_list)] if dept_list else '',
                            'reason_memo': res.get('reason_memo'),
                            'reason_type': str(res.get('reason_type')) if res.get('reason_type') else '9',
                            'pre_status': str(res.get('pre_status')),
                            'status': str(res.get('status')),
                            'main_dept_name': main_dept.id or False,
                        }
                        if res.get('handover_userid'):
                            handover_userid = self.env['hr.employee'].search([('ding_id', '=', res.get('handover_userid'))])
                            data.update({'handover_userid': handover_userid.id})
                        emp = self.env['dingtalk.employee.roster'].search([('ding_userid', '=', res.get('userid'))], limit=1)
                        if emp:
                            data.update({'emp_id': emp.id or False})
                        hrm = self.env['dingtalk.hrm.dimission.list'].search([('ding_id', '=', res.get('userid'))])
                        if hrm:
                            hrm.write(data)
                        else:
                            self.env['dingtalk.hrm.dimission.list'].create(data)
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def _get_dimission_userid_list(self, client):
        """
        获取离职员工userid列表
        :return:
        """
        dimission_list = list()
        offset = 0
        size = 50
        while True:
            try:
                result = client.employeerm.querydimission(offset=offset, size=size)
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

