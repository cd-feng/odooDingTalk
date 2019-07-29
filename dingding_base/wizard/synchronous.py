# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import base64
import json
import logging
import requests
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingSynchronous(models.TransientModel):
    _name = 'dingding.bash.data.synchronous'
    _description = "基础数据同步"
    _rec_name = 'employee'

    department = fields.Boolean(string=u'同步钉钉部门', default=True)
    employee = fields.Boolean(string=u'同步钉钉员工', default=True)
    employee_avatar = fields.Boolean(string=u'是否替换为钉钉员工头像', default=False)
    partner = fields.Boolean(string=u'同步钉钉联系人', default=True)

    @api.multi
    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        for res in self:
            if res.department:
                self.synchronous_dingding_department()
                self.synchronous_dingding_department()   # 重复的目的是先生成的子部门能关联到后生成的父部门
            if res.employee:
                self.synchronous_dingding_employee(s_avatar=res.employee_avatar)
            if res.partner:
                self.synchronous_dingding_category()
                self.synchronous_dingding_partner()

    @api.model
    def synchronous_dingding_department(self):
        """
        同步钉钉部门
        :return:
        """
        logging.info(">>>---Start 同步部门-------")
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('department_list')
        data = {'fetch_child': True, 'id': 1}
        result = self.env['dingding.api.tools'].send_get_request(url, token, data, 3)
        if result.get('errcode') == 0:
            for res in result.get('department'):
                data = {
                    'name': res.get('name'),
                    'ding_id': res.get('id'),
                }
                if res.get('parentid') != 1:
                    partner_department = self.env['hr.department'].search([('ding_id', '=', res.get('parentid'))])
                    if partner_department:
                        data.update({'parent_id': partner_department[0].id})
                h_department = self.env['hr.department'].search([('ding_id', '=', res.get('id'))])
                if h_department:
                    h_department.sudo().write(data)
                else:
                    self.env['hr.department'].create(data)
            logging.info(">>>-----End 同步部门-------")
            return True
        else:
            raise UserError("同步部门时发生意外，原因为:{}".format(result.get('errmsg')))

    @api.model
    def synchronous_dingding_employee(self, s_avatar=None):
        """
        同步钉钉部门员工列表
        :param s_avatar: 是否同步头像
        :return:
        """
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('user_listbypage')
        # 获取所有部门
        departments = self.env['hr.department'].sudo().search([('ding_id', '!=', '')])
        for department in departments:
            emp_offset = 0
            emp_size = 100
            while True:
                logging.info(">>>开始获取{}部门的员工".format(department.name))
                data = {
                    'access_token': token,
                    'department_id': department.ding_id,
                    'offset': emp_offset,
                    'size': emp_size,
                }
                result_state = self.get_dingding_employees(department, url, data, s_avatar=s_avatar)
                if result_state:
                    emp_offset = emp_offset + 1
                else:
                    break
        return True

    @api.model
    def get_dingding_employees(self, department, url, data, s_avatar=None):
        """
        创建员工
        :param department:
        :param url:
        :param data:
        :param s_avatar:
        :return:
        """
        result = requests.get(url=url, params=data, timeout=30)
        result = json.loads(result.text)
        logging.info(">>>钉钉Result:{}".format(result))
        if result.get('errcode') == 0:
            for user in result.get('userlist'):
                data = {
                    'name': user.get('name'),  # 员工名称
                    'ding_id': user.get('userid'),  # 钉钉用户Id
                    'din_unionid': user.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': user.get('mobile'),  # 手机号
                    'work_phone': user.get('tel'),  # 分机号
                    'work_location': user.get('workPlace'),  # 办公地址
                    'notes': user.get('remark'),  # 备注
                    'job_title': user.get('position'),  # 职位
                    'work_email': user.get('email'),  # email
                    'din_jobnumber': user.get('jobnumber'),  # 工号
                    'department_id': department[0].id,  # 部门
                    'din_avatar': user.get('avatar') if user.get('avatar') else '',  # 钉钉头像url
                    'din_isSenior': user.get('isSenior'),  # 高管模式
                    'din_isAdmin': user.get('isAdmin'),  # 是管理员
                    'din_isBoss': user.get('isBoss'),  # 是老板
                    'din_isLeader': user.get('isLeader'),  # 是部门主管
                    'din_isHide': user.get('isHide'),  # 隐藏手机号
                    'din_active': user.get('active'),  # 是否激活
                    'din_isLeaderInDepts': user.get('isLeaderInDepts'),  # 是否为部门主管
                    'din_orderInDepts': user.get('orderInDepts'),  # 所在部门序位
                }
                # 支持显示国际手机号
                if user.get('stateCode') != '86':
                    data.update({'mobile_phone': '+{}-{}'.format(user.get('stateCode'),user.get('mobile'))})
                if user.get('hiredDate'):
                    time_stamp = self.env['dingding.api.tools'].get_time_stamp(user.get('hiredDate'))
                    data.update({'din_hiredDate': time_stamp})
                if s_avatar and user.get('avatar'):
                    try:
                        binary_data = tools.image_resize_image_big(base64.b64encode(requests.get(user.get('avatar')).content))
                        data.update({'image': binary_data})
                    except Exception as e:
                        logging.info(">>>--------------------------------")
                        logging.info(">>>钉钉头像SSL异常:{}".format(e))
                        logging.info(">>>--------------------------------")
                if user.get('department'):
                        dep_din_ids = user.get('department')
                        dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_din_ids)])
                        data.update({'department_ids': [(6, 0, dep_list.ids)]})
                employee = self.env['hr.employee'].search(['|', ('ding_id', '=', user.get('userid')), ('mobile_phone', '=', user.get('mobile'))])
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
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('listlabelgroups')
        data = {'size': 100, 'offset': 0}
        result = self.env['dingding.api.tools'].send_post_request(url, token, data)
        if result.get('errcode') == 0:
            category_list = list()
            for res in result.get('results'):
                for labels in res.get('labels'):
                    category_list.append({
                        'name': labels.get('name'),
                        'ding_id': labels.get('id'),
                        'din_color': res.get('color'),
                        'din_category_type': res.get('name'),
                    })
            for category in category_list:
                res_category = self.env['res.partner.category'].sudo().search([('ding_id', '=', category.get('ding_id'))])
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
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('extcontact_list')
        data = {'size': 100, 'offset': 0}
        result = self.env['dingding.api.tools'].send_post_request(url, token, data)
        if result.get('errcode') == 0:
            for res in result.get('results'):
                # 获取标签
                label_list = list()
                for label in res.get('label_ids'):
                    category = self.env['res.partner.category'].sudo().search(
                        [('ding_id', '=', label)])
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
                        [('ding_id', '=', res.get('follower_user_id'))])
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

