# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkHrSynchronous(models.TransientModel):
    _name = 'dingtalk.hr.synchronous'
    _description = "基础数据同步"
    _rec_name = 'employee'

    department = fields.Boolean(string=u'钉钉部门', default=True)
    active_dept = fields.Boolean(string=u'归档不存在的部门?', default=False)
    dept_repeat = fields.Selection(string=u'部门名称重复时', selection=[('cover', '覆盖'), ('new', '新建')], default='cover')
    synchronous_dept_detail = fields.Boolean(string=u'部门详情', default=True)
    employee = fields.Boolean(string=u'钉钉员工', default=True)
    emp_repeat = fields.Selection(string=u'员工名称重复时', selection=[('cover', '覆盖'), ('new', '新建')], default='cover')

    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        self.ensure_one()
        try:
            if self.department:
                self.synchronous_dingtalk_department(self.active_dept, self.dept_repeat)
            if self.employee:
                self.synchronous_dingtalk_employee(self.emp_repeat)
            if self.synchronous_dept_detail:
                # 获取部门详情
                self.get_department_details()
        except Exception as e:
            raise UserError(e)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def synchronous_dingtalk_department(self, active_dept=None, dept_repeat=None):
        """
        同步钉钉部门
        :return:
        """
        client = dingtalk_api.get_client(self)
        result = client.department.list(fetch_child=True)
        dept_ding_ids = list()
        for res in result:
            dept_ding_ids.append(str(res.get('id')))
            data = {
                'name': res.get('name'),
                'ding_id': res.get('id'),
            }
            # 获取上级部门
            partner_department = self.env['hr.department'].search([('ding_id', '=', res.get('parentid'))], limit=1)
            if partner_department:
                data.update({'parent_id': partner_department.id})
            if dept_repeat == 'cover':
                h_department = self.env['hr.department'].search([('name', '=', res.get('name')), ('ding_id', '=', res.get('id'))])
            else:
                h_department = self.env['hr.department'].search([('ding_id', '=', res.get('id'))])
            if h_department:
                h_department.write(data)
            else:
                self.env['hr.department'].create(data)
        if active_dept:
            departments = self.env['hr.department'].sudo().search([])
            for department in departments:
                if department.ding_id not in dept_ding_ids:
                    department.write({'active': False})
                else:
                    department.write({'active': True})
        self.env.cr.commit()
        return True

    @api.model
    def get_department_details(self):
        """
        获取部门详情
        :return:
        """
        departments = self.env['hr.department'].sudo().search([('active', '=', True), ('ding_id', '!=', '')])
        client = dingtalk_api.get_client(self)
        for department in departments:
            result = client.department.get(department.ding_id)
            dept_date = dict()
            if result.get('errcode') == 0:
                if result.get('parentid') == 1:
                    dept_date['is_root'] = True
                else:
                    partner_department = self.env['hr.department'].search([('ding_id', '=', result.get('parentid'))], limit=1)
                    if partner_department:
                        dept_date['parent_id'] = partner_department.id
            if result.get('deptManagerUseridList'):
                depts = result.get('deptManagerUseridList').split("|")
                manage_users = self.env['hr.employee'].search([('ding_id', 'in', depts)])
                if manage_users:
                    dept_date.update({
                        'manager_user_ids': [(6, 0, manage_users.ids)],
                        'manager_id': manage_users[0].id
                    })
            if dept_date:
                department.write(dept_date)
        self.env.cr.commit()
        return True

    @api.model
    def synchronous_dingtalk_employee(self, emp_repeat=None):
        """
        同步钉钉部门员工列表
        :param emp_repeat: 员工名称重复选择项
        :return:
        """
        departments = self.env['hr.department'].sudo().search([('ding_id', '!=', ''), ('active', '!=', False)])
        client = dingtalk_api.get_client(self)
        # for department in departments.with_progress(msg="同步部门员工"):
        for department in departments:
            emp_offset = 0
            emp_size = 100
            while True:
                _logger.info(">>>开始获取%s部门的员工", department.name)
                result_state = self.get_dingtalk_employees(client, department, emp_offset, emp_size, emp_repeat)
                if result_state:
                    emp_offset = emp_offset + 1
                else:
                    break
        self.env.cr.commit()
        return True

    @api.model
    def get_dingtalk_employees(self, client, department, offset=0, size=100, emp_repeat=None):
        """
        获取部门成员（详情）
        :param client:
        :param department:
        :param offset:
        :param size:
        :param emp_repeat:
        :return:
        """
        try:
            result = client.user.list(department.ding_id, offset, size, order='custom')
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
                    'ding_avatar_url': user.get('avatar') if user.get('avatar') else '',  # 钉钉头像url
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
                    time_stamp = dingtalk_api.timestamp_to_local_date(self, user.get('hiredDate'))
                    data.update({'din_hiredDate': time_stamp})
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_din_ids)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                # 判断使用的方式，name查找或ding_id查找
                if emp_repeat == 'cover':
                    employee = self.env['hr.employee'].search([('name', '=', user.get('name')), ('ding_id', '=', user.get('userid'))])
                else:
                    employee = self.env['hr.employee'].search([('ding_id', '=', user.get('userid'))])
                if employee:
                    employee.sudo().write(data)
                else:
                    self.env['hr.employee'].sudo().create(data)
            return result.get('hasMore')
        except Exception as e:
            raise UserError("获取{}部门失败，原因:{}".format(department.name, e))


class DingTalkHrSynchronousPartner(models.TransientModel):
    _name = 'dingtalk.hr.synchronous.partner'
    _description = "联系人同步"
    _rec_name = 'id'

    partner_repeat = fields.Selection(string=u'联系人名称重复时', selection=[('cover', '覆盖'), ('new', '新建')], default='cover')

    def start_synchronous_partner(self):
        self.ensure_one()
        # 同步标签
        self.synchronous_dingtalk_category()
        # 同步联系人
        self.synchronous_dingtalk_partner(self.partner_repeat)
        return {'type': 'ir.actions.act_window_close'}

    def synchronous_dingtalk_category(self):
        """
        同步标签
        :return:
        """
        client = dingtalk_api.get_client(self)
        try:
            results = client.ext.listlabelgroups()
            category_list = list()
            for res in results:
                for labels in res.get('labels'):
                    category_list.append({
                        'name': labels.get('name'),
                        'ding_id': labels.get('id'),
                        'ding_category_type': res.get('name'),
                    })
            for category in category_list:
                res_category = self.env['res.partner.category'].search(
                    [('ding_id', '=', category.get('ding_id'))])
                if res_category:
                    res_category.sudo().write(category)
                else:
                    self.env['res.partner.category'].create(category)
        except Exception as e:
            raise UserError(e)

    def synchronous_dingtalk_partner(self, partner_repeat):
        """
        同步联系人
        :return:
        """
        client = dingtalk_api.get_client(self)
        try:
            results = client.ext.list(offset=0, size=100)
            for res in results:
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
                    'ding_id': res.get('userId'),  # 钉钉用户id
                    'comment': res.get('remark'),  # 备注
                    'street': res.get('address'),  # 地址
                    'mobile': res.get('mobile'),  # 手机
                    'phone': res.get('mobile'),  # 电话
                    'ding_company_name': res.get('company_name'),  # 钉钉公司名称
                }
                # 获取负责人
                if res.get('followerUserId'):
                    follower_user = self.env['hr.employee'].search([('ding_id', '=', res.get('followerUserId'))], limit=1)
                    if follower_user:
                        data.update({'ding_employee_id': follower_user.id})
                if partner_repeat == 'cover':
                    partner = self.env['res.partner'].search([('name', '=', res.get('name'))])
                else:
                    partner = self.env['res.partner'].search([('ding_id', '=', res.get('userId'))])
                if partner:
                    partner.sudo().write(data)
                else:
                    self.env['res.partner'].sudo().create(data)
        except Exception as e:
            raise UserError(e)
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class CreateResUser(models.TransientModel):
    _name = 'create.res.user'
    _description = "创建用户"

    @api.model
    def _default_domain(self):
        return [('user_id', '=', False)]

    is_all = fields.Boolean(string=u'全部员工?')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string=u'员工', domain=_default_domain)
    groups = fields.Many2many(comodel_name='res.groups', string=u'分配权限')
    ttype = fields.Selection(string=u'账号类型', selection=[('phone', '工作手机'), ('email', '工作Email')], default='phone')

    @api.onchange('is_all')
    def _onchange_is_all(self):
        for res in self:
            if res.is_all:
                emps = self.env['hr.employee'].search([('ding_id', '!=', False), ('user_id', '=', False)])
                self.employee_ids = [(6, 0, emps.ids)]
            else:
                self.employee_ids = [(2, 0, self.employee_ids.ids)]

    def create_user(self):
        """
        根据员工创建系统用户
        :return:
        """
        self.ensure_one()
        # 权限
        group_user = self.env.ref('base.group_user')[0]
        group_ids = list()
        for group in self.groups:
            group_ids.append(group.id)
        group_ids.append(group_user.id)
        for employee in self.employee_ids:
            values = {
                'active': True,
                "name": employee.name,
                'email': employee.work_email,
                'groups_id': [(6, 0, group_ids)],
                'ding_user_id': employee.ding_id,
                'ding_user_phone': employee.mobile_phone,
            }
            if self.ttype == 'email':
                if not employee.work_email:
                    raise UserError("员工{}不存在工作邮箱，无法创建用户!".format(employee.name))
                values.update({'login': employee.work_email, "password": employee.work_email})
            else:
                if not employee.mobile_phone:
                    raise UserError("员工{}办公手机为空，无法创建用户!".format(employee.name))
                values.update({'login': employee.mobile_phone, "password": employee.mobile_phone})
            domain = ['|', ('login', '=', employee.work_email), ('login', '=', employee.mobile_phone)]
            user = self.env['res.users'].sudo().search(domain, limit=1)
            if user:
                employee.write({'user_id': user.id})
            else:
                name_count = self.env['res.users'].sudo().search_count([('name', 'like', employee.name)])
                if name_count > 0:
                    user_name = employee.name + str(name_count + 1)
                    values['name'] = user_name
                user = self.env['res.users'].sudo().create(values)
                employee.write({'user_id': user.id})
        return {'type': 'ir.actions.act_window_close'}