# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import api, fields, models, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class SyncEmployee(models.TransientModel):
    _name = 'dingtalk2.syn.employee'
    _description = '员工同步'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]
    company_ids = fields.Many2many('res.company', 'dingtalk_synchronous_employee_rel', string="公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.company.id])])
    repeat_type = fields.Selection(string='主键判断', selection=RepeatType, default='id')
    is_create_user = fields.Boolean(string="创建系统用户")

    def on_synchronous(self):
        """
        同步员工信息
        :return:
        """
        self.ensure_one()
        start_time = datetime.now()
        for company_id in self.company_ids:
            dept_domain = [('ding_id', '!=', False), ('company_id', '=', company_id.id)]
            department_ids = self.env['hr.department'].sudo().search(dept_domain)
            client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
            for department in department_ids:
                cursor = 0
                size = 100
                while True:
                    if department.ding_id.find('-') != -1:
                        break
                    _logger.info(">>>开始获取%s部门的员工", department.name)
                    has_more, next_cursor = self._get_dingtalk_employee_list(client, department, cursor, size, company_id)
                    if has_more and next_cursor:
                        cursor = next_cursor
                    else:
                        break
                self._cr.commit()
        end_time = datetime.now()
        res_str = "同步员工完成，共用时：{}秒".format((end_time - start_time).seconds)
        _logger.info(res_str)

    def _get_dingtalk_employee_list(self, client, department, cursor, size, company):
        """
        获取部门员工详情
        :return: 
        """
        repeat_type = self.repeat_type
        try:
            req_result = client.post('topapi/v2/user/list', {
                'dept_id': department.ding_id,
                'cursor': cursor,
                'size': size,
                'contain_access_limit': True,
            })
        except Exception as e:
            raise exceptions.UserError(message="同步员工时发生异常：{}".format(str(e)))
        if req_result.get('errcode') != 0:
            raise exceptions.UserError(message="同步员工时发生异常：{}".format(req_result.get('errmsg')))
        result = req_result.get('result')
        employee_ids = []
        for data in result.get('list'):
            value = self.env['hr.employee'].processing_dingtalk_result(data, company.id)
            if repeat_type == 'name':
                domain = [('name', '=', data.get('name')), ('company_id', '=', company.id)]
            else:
                domain = [('ding_id', '=', data.get('userid')), ('company_id', '=', company.id)]
            employee_id = self.env['hr.employee'].search(domain)
            if employee_id:
                employee_id.write(value)
            else:
                employee_id = self.env['hr.employee'].create(value)
            employee_ids.append(employee_id)
        if self.is_create_user:
            self.create_dingtalk_user(employee_ids)
        return result.get('has_more'), result.get('next_cursor')

    @api.model
    def create_dingtalk_user(self, employee_ids):
        """
        根据创建的员工再次创建系统用户
        """
        for employee_id in employee_ids:
            if employee_id.user_id:
                continue
            try:
                user_id = self.env['res.users'].sudo().create({
                    'name': employee_id.name,
                    'login': employee_id.work_email or employee_id.ding_org_email
                    or employee_id.mobile_phone or employee_id.work_phone,
                })
            except:
                continue
            employee_id.write({'user_id': user_id.id})
