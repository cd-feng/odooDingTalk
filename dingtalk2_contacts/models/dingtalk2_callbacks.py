# -*- coding: utf-8 -*-
import logging
from odoo import models, SUPERUSER_ID, api, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class Dingtalk2Callbacks(models.AbstractModel):
    _inherit = 'dingtalk2.callbacks'

    @api.model
    def deal_dingtalk_msg(self, event_type, encrypt_result, res_company):
        """
        处理回调的消息
        :param event_type     钉钉回调类型
        :param encrypt_result 钉钉回调的消息内容
        :param res_company    回调的公司实例
        """
        if event_type == 'user_add_org':         # 通讯录用户增加
            self.get_dingtalk_employee_data(res_company, encrypt_result.get('UserId'))
        elif event_type == 'user_modify_org':    # 通讯录用户更改
            self.get_dingtalk_employee_data(res_company, encrypt_result.get('UserId'))
        elif event_type == 'user_leave_org':     # 通讯录用户离职
            self.set_dingtalk_employee_leave(res_company, encrypt_result.get('UserId'))
        elif event_type == 'org_dept_create':    # 通讯录企业部门创建
            self.get_dingtalk_department_data(res_company, encrypt_result.get('DeptId'))
        elif event_type == 'org_dept_modify':    # 通讯录企业部门修改
            self.get_dingtalk_department_data(res_company, encrypt_result.get('DeptId'))
        elif event_type == 'org_dept_remove':    # 通讯录企业部门删除
            self.set_dingtalk_department_remove(res_company, encrypt_result.get('DeptId'))
        return super(Dingtalk2Callbacks, self).deal_dingtalk_msg(event_type, encrypt_result, res_company)

    @api.model
    def get_dingtalk_employee_data(self, company_id, ding_ids):
        """
        从钉钉中获取指定用户的详情
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
        for ding_id in ding_ids:
            try:
                req_result = client.post('topapi/v2/user/get', {'userid': ding_id})
            except Exception as e:
                _logger.info("获取用户详情失败：{}".format(str(e)))
                continue
            if req_result.get('errcode') != 0:
                raise exceptions.UserError(message="获取用户详情结果失败：{}".format(req_result.get('errmsg')))
            result = req_result.get('result')
            value = self.env['hr.employee'].processing_dingtalk_result(result, company_id.id)
            employee_id = self.env['hr.employee'].search([('ding_id', '=', ding_id), ('company_id', '=', company_id.id)])
            if employee_id:
                employee_id.write(value)
            else:
                self.env['hr.employee'].create(value)

    @api.model
    def set_dingtalk_employee_leave(self, company_id, ding_ids):
        """
        设置员工为归档状态
        """
        employee_ids = self.env['hr.employee'].search([('ding_id', 'in', ding_ids), ('company_id', '=', company_id.id)])
        if employee_ids:
            employee_ids.write({'active': False})

    @api.model
    def get_dingtalk_department_data(self, company_id, dept_ids):
        """
        获取部门详情
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
        for dept_id in dept_ids:
            try:
                req_result = client.post('topapi/v2/department/get', {'dept_id': dept_id})
            except Exception as e:
                _logger.info("获取部门详情失败：{}".format(str(e)))
                continue
            if req_result.get('errcode') != 0:
                raise exceptions.UserError(message="获取部门详情结果失败：{}".format(req_result.get('errmsg')))
            result = req_result.get('result')
            value = self.env['hr.department'].processing_dingtalk_dept_result(result, company_id.id)
            domain = [('ding_id', '=', dept_id), ('company_id', '=', company_id.id)]
            department_id = self.env['hr.department'].search(domain)
            if department_id:
                department_id.write(value)
            else:
                self.env['hr.department'].create(value)

    @api.model
    def set_dingtalk_department_remove(self, company_id, dept_ids):
        """
        设置部门为归档状态
        """
        department_ids = self.env['hr.department'].search([('ding_id', 'in', dept_ids), ('company_id', '=', company_id.id)])
        if department_ids:
            department_ids.write({'active': False})

