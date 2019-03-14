# -*- coding: utf-8 -*-
import json
import logging
import time

import requests
from requests import ReadTimeout

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

""" 钉钉部门功能模块 """


# 拓展部门员工
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    din_id = fields.Char(string='钉钉用户Id')
    din_unionid = fields.Char(string='钉钉唯一标识')
    din_jobnumber = fields.Char(string='钉钉员工工号')
    din_hiredDate = fields.Date(string='入职时间')

    # 重写创建方法，检查是否创建时上传至钉钉
    @api.model
    def create(self, values):
        din_create_employee = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_create_employee')
        if din_create_employee:
            userid = self.create_din_employee(values)
            values['din_id'] = userid
        return super(HrEmployee, self).create(values)

    @api.model
    def create_din_employee(self, values):
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_create')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        # 获取部门din_id
        department_list = list()
        if values.get('department_id'):
            department = self.env['hr.department'].sudo().search([('id', '=', values.get('department_id'))])
            if department:
                department_list.append(department[0].din_id)
        else:
            raise UserError("请选择员工部门!")
        data = {
            'name': values.get('name'),   # 名称
            'department': department_list,   # 部门
            'position': values.get('job_title'),   # 职位
            'mobile': values.get('mobile_phone'),   # 手机
            'tel': values.get('work_phone'),   # 手机
            'workPlace': values.get('work_location'),   # 办公地址
            'remark': values.get('notes'),   # 备注
            'email': values.get('work_email'),   # 备注
            'jobnumber': values.get('din_jobnumber'),   # 工号
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(result)
            if result.get('errcode') == 0:
                return result.get('userid')
            else:
                raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传员工至钉钉超时！")


# 同步钉钉与部门员工功能模型
class DinDinSynchronousEmployee(models.TransientModel):
    _name = 'dindin.synchronous.employee'
    _description = "同步钉钉部门员工功能模型"

    @api.multi
    def start_synchronous_employee(self):
        logging.info("同步钉钉部门员工列表")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_listbypage')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        # 获取所有部门
        departments = self.env['hr.department'].sudo().search([('din_id', '!=', '')])
        for department in departments:
            logging.info(">>>开始获取{}部门的员工".format(department.name))
            data = {
                'access_token': token,
                'department_id': department[0].din_id,
                'offset': 0,
                'size': 100,
            }
            result = requests.get(url=url, params=data, timeout=20)
            logging.info(">>>获取钉钉部门{}员工结果:{}".format(department.name,result.text))
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                for user in result.get('userlist'):
                    if user.get('hiredDate'):
                        tl = time.localtime(float(user.get('hiredDate'))/1000)
                    data = {
                        'name': user.get('name'),  # 员工名称
                        'din_id': user.get('userid'),  # 钉钉用户Id
                        'din_unionid': user.get('unionid'),  # 钉钉唯一标识
                        'mobile_phone': user.get('mobile'),  # 手机号
                        'work_phone': user.get('tel'),  # 分机号
                        'work_location': user.get('workPlace'),  # 办公地址
                        'notes': user.get('remark'),  # 备注
                        'job_title': user.get('position'),  # 职位
                        'work_email': user.get('email'),  # email
                        'din_jobnumber': user.get('jobnumber'),  # 工号
                        'din_hiredDate': time.strftime('%Y-%m-%d') if tl else False,  # 入职时间
                        'department_id': department[0].id,  # 部门
                    }
                    employee = self.env['hr.employee'].search([('din_id', '=', user.get('userid'))])
                    if employee:
                        employee.sudo().write(data)
                    else:
                        self.env['hr.employee'].sudo().create(data)
                    logging.info(">>>同步部门员工结束")
            else:
                logging.info(">>>获取部门员工失败，原因为:{}".format(result.get('errmsg')))
                raise UserError("获取部门员工失败，原因为:{}".format(result.get('errmsg')))
