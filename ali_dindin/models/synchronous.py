# -*- coding: utf-8 -*-
import base64
import json
import logging
import time
import requests
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingSynchronous(models.TransientModel):
    _name = 'dingding.bash.data.synchronous'
    _description = "基础数据同步"
    _rec_name = 'employee'

    department = fields.Boolean(string=u'钉钉部门同步', default=True)
    employee = fields.Boolean(string=u'钉钉员工同步', default=True)
    partner = fields.Boolean(string=u'钉钉联系人同步', default=True)

    @api.multi
    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        for res in self:
            if res.department:
                self.synchronous_dingding_department()
            if res.employee:
                self.synchronous_dingding_employee()
            if res.partner:
                self.synchronous_dingding_category()
                self.synchronous_dingding_partner()

    @api.model
    def synchronous_dingding_department(self):
        """
        同步钉钉部门
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'department_list')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {'id': 1}
        result = requests.get(url="{}{}".format(url, token), params=data, timeout=5)
        result = json.loads(result.text)
        if result.get('errcode') == 0:
            for res in result.get('department'):
                data = {
                    'name': res.get('name'),
                    'din_id': res.get('id'),
                }
                if res.get('parentid') != 1:
                    partner_department = self.env['hr.department'].search(
                        [('din_id', '=', res.get('parentid'))])
                    if partner_department:
                        data.update({'parent_id': partner_department[0].id})
                h_department = self.env['hr.department'].search(
                    ['|', ('din_id', '=', res.get('id')), ('name', '=', res.get('name'))])
                if h_department:
                    h_department.sudo().write(data)
                else:
                    self.env['hr.department'].create(data)
            return True
        else:
            raise UserError("同步部门时发生意外，原因为:{}".format(result.get('errmsg')))

    @api.model
    def synchronous_dingding_employee(self):
        """
        同步钉钉部门员工列表
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_listbypage')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        # 获取所有部门
        departments = self.env['hr.department'].sudo().search([('din_id', '!=', '')])
        for department in departments:
            emp_offset = 0
            emp_size = 100
            while True:
                logging.info(">>>开始获取{}部门的员工".format(department.name))
                data = {
                    'access_token': token,
                    'department_id': department[0].din_id,
                    'offset': emp_offset,
                    'size': emp_size,
                }
                result_state = self.get_dingding_employees(department, url, data)
                if result_state:
                    emp_offset = emp_offset + 1
                else:
                    break
        return True

    @api.model
    def get_dingding_employees(self, department, url, data):
        result = requests.get(url=url, params=data, timeout=5)
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
                }
                if user.get('hiredDate'):
                    time_stamp = self.get_time_stamp(user.get('hiredDate'))
                    data.update({
                        'din_hiredDate': time_stamp,
                    })
                if user.get('avatar'):
                    try:
                        binary_data = tools.image_resize_image_big(base64.b64encode(requests.get(user.get('avatar')).content))
                        data.update({'image': binary_data})
                    except Exception as e:
                        logging.info(">>>--------------------------------")
                        logging.info(">>>SSL异常:{}".format(e))
                        logging.info(">>>--------------------------------")
                employee = self.env['hr.employee'].search(['|', ('din_id', '=', user.get('userid')), ('name', '=', user.get('name'))])
                if employee:
                    employee.sudo().write(data)
                else:
                    self.env['hr.employee'].sudo().create(data)
            return result.get('hasMore')
        else:
            raise UserError("同步部门员工时发生意外，原因为:{}".format(result.get('errmsg')))

    @api.model
    def synchronous_dingding_category(self):
        """
        同步钉钉联系人标签
        :return:
        """
        logging.info(">>>同步钉钉联系人标签")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'listlabelgroups')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        headers = {'Content-Type': 'application/json'}
        data = {
            'size': 100,
            'offset': 0
        }
        result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
        result = json.loads(result.text)
        if result.get('errcode') == 0:
            category_list = list()
            for res in result.get('results'):
                for labels in res.get('labels'):
                    category_list.append({
                        'name': labels.get('name'),
                        'din_id': labels.get('id'),
                        'din_color': res.get('color'),
                        'din_category_type': res.get('name'),
                    })
            for category in category_list:
                res_category = self.env['res.partner.category'].sudo().search([('din_id', '=', category.get('din_id'))])
                if res_category:
                    res_category.sudo().write(category)
                else:
                    self.env['res.partner.category'].sudo().create(category)
            return True
        else:
            raise UserError("同步联系人标签时发生错误，原因为:{}".format(result.get('errmsg')))

    @api.model
    def synchronous_dingding_partner(self):
        """
        同步钉钉联系人列表
        :return:
        """
        logging.info(">>>同步钉钉联系人列表start")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'extcontact_list')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        headers = {'Content-Type': 'application/json'}
        data = {
            'size': 100,
            'offset': 0
        }
        result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
        result = json.loads(result.text)
        if result.get('errcode') == 0:
            for res in result.get('results'):
                # 获取标签
                label_list = list()
                for label in res.get('label_ids'):
                    category = self.env['res.partner.category'].sudo().search(
                        [('din_id', '=', label)])
                    if category:
                        label_list.append(category[0].id)
                data = {
                    'name': res.get('name'),
                    'function': res.get('title'),
                    'category_id': [(6, 0, label_list)],  # 标签
                    'din_userid': res.get('userid'),  # 钉钉用户id
                    'comment': res.get('remark'),  # 备注
                    'street': res.get('address'),  # 地址
                    'mobile': res.get('mobile'),  # 手机
                    'phone': res.get('mobile'),  # 电话
                    'din_company_name': res.get('company_name'),  # 钉钉公司名称
                }
                # 获取负责人
                if res.get('follower_user_id'):
                    follower_user = self.env['hr.employee'].sudo().search(
                        [('din_id', '=', res.get('follower_user_id'))])
                    data.update({'din_employee_id': follower_user[0].id if follower_user else ''})
                # 根据userid查询联系人是否存在
                partner = self.env['res.partner'].sudo().search(['|', ('din_userid', '=', res.get('userid')), ('name', '=', res.get('name'))])
                if partner:
                    partner.sudo().write(data)
                else:
                    self.env['res.partner'].sudo().create(data)
            return True
        else:
            raise UserError("同步钉钉联系人失败，原因为:{}".format(result.get('errmsg')))

    @api.model
    def get_time_stamp(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000)
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
