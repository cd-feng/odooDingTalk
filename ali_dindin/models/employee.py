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
    din_sy_state = fields.Boolean(string=u'同步标识', default=False)

    # 重写创建方法，检查是否创建时上传至钉钉
    @api.model
    def create(self, values):
        if not values.get('din_sy_state'):
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
            'name': values.get('name'),  # 名称
            'department': department_list,  # 部门
            'position': values.get('job_title') if values.get('job_title') else '',  # 职位
            'mobile': values.get('mobile_phone') if values.get('mobile_phone') else '',  # 手机
            'tel': values.get('work_phone') if values.get('work_phone') else '',  # 手机
            'workPlace': values.get('work_location') if values.get('work_location') else '',  # 办公地址
            'remark': values.get('notes') if values.get('notes') else '',  # 备注
            'email': values.get('work_email') if values.get('work_email') else '',  # 邮箱
            'jobnumber': values.get('din_jobnumber') if values.get('din_jobnumber') else '',  # 工号
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

    # 重写修改方法
    @api.multi
    def write(self, values):
        id = self.id
        super(HrEmployee, self).write(values)
        if not values.get('din_sy_state'):
            din_update_employee = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_update_employee')
            if din_update_employee:
                emp = self.env['hr.employee'].sudo().search([('id', '=', id)])
                self.update_din_employee(emp[0])
        return True

    @api.model
    def update_din_employee(self, emp):
        """修改员工时同步至钉钉"""
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_update')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        # 获取部门din_id
        department_list = list()
        if not emp.department_id:
            raise UserError("请选择员工部门!")
        data = {
            'userid': emp.din_id,  # userid
            'name': emp.name,  # 名称
            'department': department_list.append(emp.department_id.din_id),  # 部门
            'position': emp.job_title if emp.job_title else '',  # 职位
            'mobile': emp.mobile_phone if emp.mobile_phone else '',  # 手机
            'tel': emp.work_phone if emp.work_phone else '',  # 手机
            'workPlace': emp.work_location if emp.work_location else '',  # 办公地址
            'remark': emp.notes if emp.notes else '',  # 备注
            'email': emp.work_email if emp.work_email else '',  # 邮箱
            'jobnumber': emp.din_jobnumber if emp.din_jobnumber else '',  # 工号
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(result)
            if result.get('errcode') == 0:
                emp.message_post(body=u"新的信息已同步更新至钉钉", message_type='notification')
            else:
                raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传员工至钉钉超时！")

    # 重写删除方法
    @api.multi
    def unlink(self):
        userid = self.din_id
        super(HrEmployee, self).unlink()
        din_delete_employee = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_employee')
        if din_delete_employee:
            self.delete_din_employee(userid)
        return True

    @api.model
    def delete_din_employee(self, userid):
        """删除钉钉用户"""
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_delete')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'userid': userid,  # userid
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
            result = json.loads(result.text)
            logging.info("user_delete:{}".format(result))
            if result.get('errcode') != 0:
                raise UserError('删除钉钉用户时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传员工至钉钉超时！")

    @api.multi
    def update_employee_dindin(self):
        """手动上传至钉钉"""
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_create')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            # 获取部门din_id
            department_list = list()
            if res.department_id:
                department = self.env['hr.department'].sudo().search([('id', '=', res.department_id.id)])
                if department:
                    department_list.append(department[0].din_id)
            else:
                raise UserError("请选择员工部门!")
            data = {
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else '',  # 手机
                'tel': res.work_phone if res.work_phone else '',  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    res.sudo().write({'din_id': result.get('userid')})
                    res.message_post(body=u"新的信息已同步更新至钉钉", message_type='notification')
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
            logging.info(">>>获取钉钉部门{}员工结果:{}".format(department.name, result.text))
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                for user in result.get('userlist'):
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
                        'department_id': department[0].id,  # 部门
                        'din_sy_state': True,  # 同步标识
                    }
                    if user.get('hiredDate'):
                        tl = time.localtime(float(user.get('hiredDate')) / 1000)
                        data.update({
                            'din_hiredDate': time.strftime('%Y-%m-%d', tl) if tl else False,  # 入职时间
                        })
                    employee = self.env['hr.employee'].search([('din_id', '=', user.get('userid'))])
                    if employee:
                        employee.sudo().write(data)
                    else:
                        self.env['hr.employee'].sudo().create(data)
                    logging.info(">>>同步部门员工结束")
            else:
                logging.info(">>>获取部门员工失败，原因为:{}".format(result.get('errmsg')))
                raise UserError("获取部门员工失败，原因为:{}".format(result.get('errmsg')))
