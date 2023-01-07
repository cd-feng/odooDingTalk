# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import fields, models, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class SynHrDepartment(models.TransientModel):
    _name = 'dingtalk2.syn.department'
    _description = '部门同步'

    company_ids = fields.Many2many('res.company', 'dingtalk2_syns_and_department_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.company.id])])
    repeat_type = fields.Selection(string='主键判断', selection=[('name', '以名称判断'), ('id', '以钉钉ID')], default='id')

    def on_synchronous(self):
        """
        同步部门信息
        :return:
        """
        start_time = datetime.now()  # 开始的时间
        self.ensure_one()
        # 获取部门列表
        self._synchronous_department(self.company_ids)
        self._cr.commit()
        # 获取部门详情
        self._get_department_info(self.company_ids)
        end_time = datetime.now()
        _logger.debug("同步部门列表完成，共用时：{}秒".format((end_time - start_time).seconds))

    def _synchronous_department(self, company_ids):
        """
        处理同步部门信息
        :return:
        """
        for company_id in company_ids:
            try:
                client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
                req_result = client.department.list(fetch_child=True)
            except Exception as e:
                raise exceptions.UserError("同步部门时发生异常，原因为：{}".format(str(e)))
            department_model = self.env['hr.department']
            number = 1
            for res in req_result:
                _logger.info("正在处理第%s条数据，-> %s" % (number, res))
                data = {
                    'company_id': company_id.id,
                    'name': res.get('name'),
                    'ding_id': res.get('id'),
                }
                if self.repeat_type == 'name':
                    domain = [('name', '=', res.get('name')), ('company_id', '=', company_id.id)]
                else:
                    domain = [('ding_id', '=', res.get('id')), ('company_id', '=', company_id.id)]
                hr_department = department_model.search(domain)
                if hr_department:
                    hr_department.write(data)
                else:
                    department_model.create(data)
                number += 1

    def _get_department_info(self, company_ids):
        """
        获取部门详情
        """
        department_model = self.env['hr.department']
        employee_model = self.env['hr.employee']
        for company_id in company_ids:
            department_ids = department_model.search([('ding_id', '!=', False)])
            try:
                client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
            except Exception as e:
                raise exceptions.UserError("同步部门时发生异常，原因为：{}".format(str(e)))
            for department_id in department_ids:
                try:
                    req_result = client.post('topapi/v2/department/get', {'dept_id': department_id.ding_id})
                except Exception as e:
                    raise exceptions.UserError("同步部门时发生异常，原因为：{}".format(str(e)))
                if req_result.get('errcode') == 0:
                    result = req_result.get('result')
                    value = {}
                    # 上级部门
                    parent_id = result.get('parent_id')
                    if parent_id != 1:
                        parent_dept = self.env['hr.department'].get_dingtalk_department_id(parent_id, company_id.id)
                        if parent_dept:
                            value['parent_id'] = parent_dept.id
                    # 部门主管
                    dept_manager_userid_list = result.get('dept_manager_userid_list')
                    manager_user_ids = employee_model.search([('ding_id', 'in', dept_manager_userid_list)])
                    if manager_user_ids:
                        value['manager_user_ids'] = [(6, 0, manager_user_ids.ids)]
                    if value:
                        department_id.write(value)

