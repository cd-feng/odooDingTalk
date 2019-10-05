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

    department = fields.Boolean(string=u'钉钉部门', default=True)
    employee = fields.Boolean(string=u'钉钉员工', default=True)
    employee_avatar = fields.Boolean(string=u'替换钉钉员工头像', default=False)
    partner = fields.Boolean(string=u'钉钉联系人', default=True)
    synchronous_dept_detail = fields.Boolean(string=u'部门详情', default=True)
    
    
    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        self.ensure_one()
        try:
            if self.department:
                self.synchronous_dingding_department()
            if self.employee:
                self.synchronous_dingding_employee(s_avatar=self.employee_avatar)
            if self.partner:
                self.synchronous_dingding_category()    # 同步标签
                self.synchronous_dingding_partner()     # 同步员工
            if self.synchronous_dept_detail:
                # 获取部门详情
                self.get_department_details()
        except Exception as e:
            raise UserError(e)

    @api.model
    def synchronous_dingding_department(self):
        """
        同步钉钉部门
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        result = din_client.department.list(fetch_child=True)
        dept_ding_ids = list()
        for res in result:
            dept_ding_ids.append(str(res.get('id')))
            data = {
                'name': res.get('name'),
                'ding_id': res.get('id'),
            }
            h_department = self.env['hr.department'].search([('ding_id', '=', res.get('id')), ('active', '=', True)])
            if h_department:
                h_department.write(data)
            else:
                self.env['hr.department'].create(data)
        # 情况：当在钉钉端删除了部门后，那么在odoo原还存在该部门，所以在同步完成后，在检查一遍，将存在的保留，不存在的部门进行归档
        departments = self.env['hr.department'].sudo().search(['|', ('active', '=', False), ('active', '=', True)])
        for department in departments:
            ding_id = department.ding_id
            if ding_id not in dept_ding_ids:
                department.write({'active': False})
            else:
                department.write({'active': True})
        return True

    @api.model
    def get_department_details(self):
        """
        获取部门详情
        :return:
        """
        departments = self.env['hr.department'].sudo().search([('active', '=', True), ('ding_id', '!=', '')])
        din_client = self.env['dingding.api.tools'].get_client()
        for department in departments:
            result = din_client.department.get(department.ding_id)
            if result.get('errcode') == 0:
                if result.get('parentid') != 1:
                    partner_department = self.env['hr.department'].search([('ding_id', '=', result.get('parentid'))])
                    if partner_department:
                        self._cr.execute("UPDATE hr_department SET parent_id=%s WHERE id=%s" % (partner_department.id, department.id))
            dept_manageusers = result.get('deptManagerUseridList')
            if dept_manageusers:
                depts = dept_manageusers.split("|")
                manage_users = self.env['hr.employee'].search([('ding_id', 'in', depts)])
                department.write({'manager_user_ids': [(6, 0, manage_users.ids)], 'manager_id': manage_users[0].id})
        return True

    @api.model
    def synchronous_dingding_employee(self, s_avatar=None):
        """
        同步钉钉部门员工列表
        :param s_avatar: 是否同步头像
        :return:
        """
        # 获取所有部门
        departments = self.env['hr.department'].sudo().search([('ding_id', '!=', ''), ('active', '=', True)])
        din_client = self.env['dingding.api.tools'].get_client()
        for department in departments:
            emp_offset = 0
            emp_size = 100
            while True:
                logging.info(">>>开始获取%s部门的员工", department.name)
                result_state = self.get_dingding_employees(din_client, department, emp_offset, emp_size, s_avatar=s_avatar)
                if result_state:
                    emp_offset = emp_offset + 1
                else:
                    break
        return True

    @api.model
    def get_dingding_employees(self, din_client, department, offset=0, size=100, s_avatar=None):
        """
        获取部门成员（详情）
        :param din_client:
        :param department:
        :param offset:
        :param size:
        :param s_avatar:
        :return:
        """
        try:
            result = din_client.user.list(department.ding_id, offset, size, order='custom')
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
                    data.update({'mobile_phone': '+{}-{}'.format(user.get('stateCode'), user.get('mobile'))})
                if user.get('hiredDate'):
                    time_stamp = self.env['dingding.api.tools'].get_time_stamp(user.get('hiredDate'))
                    data.update({'din_hiredDate': time_stamp})
                if s_avatar and user.get('avatar'):
                    try:
                        binary_data = tools.image_resize_image_big(
                            base64.b64encode(requests.get(user.get('avatar')).content))
                        data.update({'image': binary_data})
                    except Exception as e:
                        logging.info(">>>--------------------------------")
                        logging.info(">>>SSL异常:%s", e)
                        logging.info(">>>--------------------------------")
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_din_ids)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                employee = self.env['hr.employee'].search([('ding_id', '=', user.get('userid'))])
                if employee:
                    employee.sudo().write(data)
                else:
                    self.env['hr.employee'].sudo().create(data)
            return result.get('hasMore')
        except Exception as e:
            raise UserError(e)

    # 留着备用
    @api.model
    def synchronous_dingding_employee_v2(self, s_avatar=None):
        """
        同步钉钉部门员工列表
        :param s_avatar: 是否同步头像
        :return:
        """
        # 获取所有部门
        departments = self.env['hr.department'].sudo().search([('ding_id', '!=', ''), ('active', '=', True)])
        din_client = self.env['dingding.api.tools'].get_client()
        ding_user_list = list()
        for department in departments:
            emp_offset = 0
            emp_size = 100
            while True:
                logging.info(">>>开始获取%s部门的员工", department.name)
                result_state, user_list = self.get_dingding_employees_v2(din_client, department, ding_user_list, emp_offset, emp_size, s_avatar=s_avatar)
                if result_state:
                    emp_offset = emp_offset + 1
                    ding_user_list = user_list
                else:
                    break
        return True

    @api.model
    def get_dingding_employees_v2(self, din_client, department, ding_user_list, offset=0, size=100, s_avatar=None):
        """
        获取部门成员（详情）
        :param din_client:
        :param department:
        :param offset:
        :param size:
        :param s_avatar:
        :return:
        """
        try:
            result = din_client.user.list(department.ding_id, offset, size, order='custom')
            user_list = list()
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
                    data.update({'mobile_phone': '+{}-{}'.format(user.get('stateCode'), user.get('mobile'))})
                if user.get('hiredDate'):
                    time_stamp = self.env['dingding.api.tools'].get_time_stamp(user.get('hiredDate'))
                    data.update({'din_hiredDate': time_stamp})
                if s_avatar and user.get('avatar'):
                    try:
                        binary_data = tools.image_resize_image_big(
                            base64.b64encode(requests.get(user.get('avatar')).content))
                        data.update({'image': binary_data})
                    except Exception as e:
                        logging.info(">>>--------------------------------")
                        logging.info(">>>SSL异常:%s", e)
                        logging.info(">>>--------------------------------")
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_din_ids)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                if user.get('userid') not in ding_user_list:
                    user_list.append(data)
                    ding_user_list.append(user.get('userid'))
                    # logging.info(">>>获取钉钉用户集结果%s", ding_user_list)
            # 批量新建员工，未做已存在记录检查
            self.env['hr.employee'].sudo().create(user_list)
            return result.get('hasMore'), ding_user_list
        except Exception as e:
            raise UserError(e)

    @api.model
    def synchronous_dingding_category(self):
        """
        同步钉钉联系人标签
        :return:
        """
        logging.info(">>>同步钉钉联系人标签")
        din_client = self.env['dingding.api.tools'].get_client()
        try:
            result = din_client.ext.listlabelgroups(offset=0, size=100)
            category_list = list()
            for res in result:
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
        except Exception as e:
            raise UserError(e)

    @api.model
    def synchronous_dingding_partner(self):
        """
        同步钉钉联系人列表
        :return:
        """
        logging.info(">>>同步钉钉联系人列表start")
        din_client = self.env['dingding.api.tools'].get_client()
        try:
            result = din_client.ext.list(offset=0, size=100)
            logging.info(result)
            for res in result:
                # 获取标签
                label_list = list()
                for label in res.get('labelIds'):
                    category = self.env['res.partner.category'].sudo().search([('ding_id', '=', label)])
                    if category:
                        label_list.append(category[0].id)
                data = {
                    'name': res.get('name'),
                    'function': res.get('title'),
                    'category_id': [(6, 0, label_list)],  # 标签
                    'din_userid': res.get('userId'),  # 钉钉用户id
                    'comment': res.get('remark'),  # 备注
                    'street': res.get('address'),  # 地址
                    'mobile': res.get('mobile'),  # 手机
                    'phone': res.get('mobile'),  # 电话
                    'din_company_name': res.get('company_name'),  # 钉钉公司名称
                }
                # 获取负责人
                if res.get('follower_user_id'):
                    follower_user = self.env['hr.employee'].sudo().search([('ding_id', '=', res.get('follower_user_id'))])
                    data.update({'din_employee_id': follower_user[0].id if follower_user else ''})
                # 根据userid查询联系人是否存在
                partner = self.env['res.partner'].sudo().search(
                    ['|', ('din_userid', '=', res.get('userId')), ('name', '=', res.get('name'))])
                if partner:
                    partner.sudo().write(data)
                else:
                    self.env['res.partner'].sudo().create(data)
            return True
        except Exception as e:
            raise UserError(e)
