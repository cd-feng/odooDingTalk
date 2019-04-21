# -*- coding: utf-8 -*-
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AddDingDingEmployee(models.TransientModel):
    _name = 'dingding.add.employee'
    _description = '添加待入职员工'

    name = fields.Char(string='员工姓名', required=True)
    mobile = fields.Char(string='手机号', required=True)
    pre_entry_time = fields.Datetime(string=u'预期入职时间', required=True)
    dept_id = fields.Many2one(comodel_name='hr.department', string=u'入职部门', required=True)

    @api.multi
    def add_employee(self):
        """
        添加待入职员工
        :return:
        """
        logging.info(">>>添加待入职员工start")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'hrm_addpreentry')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        for res in self:
            if not res.dept_id.din_id:
                raise UserError("所选部门在钉钉中不存在!")
            user = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            data = {
                'param': {
                    'name': res.name,
                    'mobile': res.mobile,
                    'pre_entry_time': str(res.pre_entry_time),
                    'op_userid': user[0].din_id if user else '',
                    'extend_info': {'depts': res.dept_id.din_id},
                }
            }
            hr_emp = self.env['hr.employee'].sudo().create({
                'name': res.name,
                'mobile_phone': res.mobile,
                'work_phone': res.mobile,
                'department_id': res.dept_id.id,
                'din_hiredDate': res.pre_entry_time,
                'work_status': 1,
            })
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    hr_emp.sudo().write({'din_id': result.get('userid')})
                else:
                    raise UserError("添加失败,原因:{}!".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        logging.info(">>>添加待入职员工end")

