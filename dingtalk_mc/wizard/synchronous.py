# -*- coding: utf-8 -*-
import logging
import threading
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingTalkMcSynchronous(models.TransientModel):
    _name = 'dingtalk.mc.synchronous'
    _description = "组织结构同步"
    _rec_name = 'employee'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]

    company_ids = fields.Many2many('res.company', 'dingtalk_mc_companys_rel', string="要同步的公司", required=True)
    department = fields.Boolean(string=u'钉钉部门', default=True)
    synchronous_dept_detail = fields.Boolean(string=u'部门详情', default=False)
    repeat_type = fields.Selection(string=u'判断唯一', selection=RepeatType, default='name')
    employee = fields.Boolean(string=u'钉钉员工', default=True)

    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        self.ensure_one()
        try:
            if self.department:
                self.synchronous_dingtalk_department(self.repeat_type)
            if self.employee:
                self.synchronous_dingtalk_employee(self.repeat_type)
            if self.synchronous_dept_detail:
                self.get_department_details()
        except Exception as e:
            raise UserError(e)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def synchronous_dingtalk_department(self, repeat_type=None):
        """
        同步钉钉部门
        :return:
        """
        for company in self.company_ids:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            result = client.department.list(fetch_child=True)
            for res in result:
                data = {
                    'company_id': company.id,
                    'name': res.get('name'),
                    'ding_id': res.get('id'),
                }
                if repeat_type == 'name':
                    domain = [('name', '=', res.get('name')), ('company_id', '=', company.id)]
                else:
                    domain = [('ding_id', '=', res.get('id')), ('company_id', '=', company.id)]
                h_department = self.env['hr.department'].sudo().search(domain)
                if h_department:
                    h_department.sudo().write(data)
                else:
                    self.env['hr.department'].sudo().create(data)
            self.env.cr.commit()
        return True

    def get_department_details(self):
        """
        获取部门详情
        :return:
        """
        for company in self.company_ids:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            departments = self.env['hr.department'].sudo().search([('company_id', '=', company.id), ('ding_id', '!=', '')])
            for dept in departments:
                result = client.department.get(dept.ding_id)
                dept_date = dict()
                if result.get('errcode') == 0:
                    if result.get('parentid') == 1:
                        dept_date['is_root'] = True
                    else:
                        doamin = [('ding_id', '=', result.get('parentid')), ('company_id', '=', company.id)]
                        partner_dept = self.env['hr.department'].sudo().search(doamin, limit=1)
                        if partner_dept:
                            dept_date['parent_id'] = partner_dept.id
                if result.get('deptManagerUseridList'):
                    depts = result.get('deptManagerUseridList').split("|")
                    manage_users = self.env['hr.employee'].sudo().search([('ding_id', 'in', depts), ('company_id', '=', company.id)])
                    dept_date.update({
                        'manager_user_ids': [(6, 0, manage_users.ids)],
                        'manager_id': manage_users[0].id
                    })
                if dept_date:
                    dept.sudo().write(dept_date)
            self.env.cr.commit()
        return True

    def synchronous_dingtalk_employee(self, repeat_type=None):
        """
        同步钉钉部门员工列表
        :return:
        """
        for company in self.company_ids:
            departments = self.env['hr.department'].sudo().search([('ding_id', '!=', ''), ('company_id', '=', company.id)])
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            for dept in departments:
                emp_offset = 0
                emp_size = 100
                while True:
                    _logger.info(">>>开始获取%s部门的员工", dept.name)
                    result_state = self.get_dingtalk_employees(client, dept, emp_offset, emp_size, company, repeat_type)
                    if result_state:
                        emp_offset += emp_size + 1
                    else:
                        break
            self.env.cr.commit()
        return True

    def get_dingtalk_employees(self, client, dept, offset, size, company, repeat_type=None):
        """
        获取部门成员（详情）
        :param client:
        :param dept:
        :param offset:
        :param size:
        :param company:
        :param repeat_type:
        :return:
        """
        try:
            result = client.user.list(dept.ding_id, offset, size, order='custom')
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
                    'department_id': dept.id,  # 部门
                    'ding_avatar_url': user.get('avatar') if user.get('avatar') else '',  # 钉钉头像url
                    'din_isSenior': user.get('isSenior'),  # 高管模式
                    'din_isAdmin': user.get('isAdmin'),  # 是管理员
                    'din_isBoss': user.get('isBoss'),  # 是老板
                    'din_isLeader': user.get('isLeader'),  # 是部门主管
                    'din_isHide': user.get('isHide'),  # 隐藏手机号
                    'din_active': user.get('active'),  # 是否激活
                    'din_isLeaderInDepts': user.get('isLeaderInDepts'),  # 是否为部门主管
                    'din_orderInDepts': user.get('orderInDepts'),  # 所在部门序位
                    'company_id': company.id
                }
                # 支持显示国际手机号
                if user.get('stateCode') != '86':
                    data.update({'mobile_phone': '+{}-{}'.format(user.get('stateCode'), user.get('mobile'))})
                if user.get('hiredDate'):
                    time_stamp = dt.timestamp_to_local_date(user.get('hiredDate'), self)
                    data.update({'din_hiredDate': time_stamp})
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_din_ids), ('company_id', '=', company.id)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                if repeat_type == 'name':
                    domain = [('name', '=', user.get('name')), ('company_id', '=', company.id)]
                else:
                    domain = [('ding_id', '=', user.get('userid')), ('company_id', '=', company.id)]
                employee = self.env['hr.employee'].sudo().search(domain)
                if employee:
                    employee.sudo().write(data)
                else:
                    self.env['hr.employee'].sudo().create(data)
            return result.get('hasMore')
        except Exception as e:
            raise UserError(e)


class DingTalkMCSynchronousPartner(models.TransientModel):
    _name = 'dingtalk.mc.synchronous.partner'
    _description = "联系人同步"
    _rec_name = 'id'

    company_ids = fields.Many2many('res.company', 'dingtalk_mc_partner_companys_rel', string="要同步的公司", required=True)

    def start_synchronous_partner(self):
        self.ensure_one()
        for company in self.company_ids:
            # 同步标签
            self.synchronous_dingtalk_category(company)
            # 同步联系人
            self.synchronous_dingtalk_partner(company)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def synchronous_dingtalk_category(self, company):
        """
        同步标签
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            results = client.ext.listlabelgroups()
            category_list = list()
            for res in results:
                for labels in res.get('labels'):
                    category_list.append({
                        'name': labels.get('name'),
                        'ding_id': labels.get('id'),
                        'ding_category_type': res.get('name'),
                        'company_id': company.id,
                    })
            for category in category_list:
                res_category = self.env['res.partner.category'].sudo().search(
                    [('ding_id', '=', category.get('ding_id')), ('company_id', '=', company.id)])
                if res_category:
                    res_category.sudo().write(category)
                else:
                    self.env['res.partner.category'].sudo().create(category)
        except Exception as e:
            raise UserError(e)

    def synchronous_dingtalk_partner(self, company):
        """
        同步联系人
        :param company:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            results = client.ext.list(offset=0, size=100)
            _logger.info(results)
            for res in results:
                # 获取标签
                label_list = list()
                for label in res.get('labelIds'):
                    category = self.env['res.partner.category'].sudo().search([('ding_id', '=', label), ('company_id', '=', company.id)], limit=1)
                    if category:
                        label_list.append(category.id)
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
                    'company_id': company.id
                }
                # 获取负责人
                if res.get('followerUserId'):
                    follower_user = self.env['hr.employee'].sudo().search([('ding_id', '=', res.get('followerUserId')), ('company_id', '=', company.id)], limit=1)
                    if follower_user:
                        data.update({'ding_employee_id': follower_user.id})
                partner = self.env['res.partner'].sudo().search([('ding_id', '=', res.get('userId')), ('company_id', '=', company.id)])
                if partner:
                    partner.sudo().write(data)
                else:
                    self.env['res.partner'].sudo().create(data)
        except Exception as e:
            raise UserError(e)
        return


class CreateResUser(models.TransientModel):
    _name = 'create.mc.res.user'
    _description = "创建用户"

    company_id = fields.Many2one(comodel_name='res.company', string="所属公司", required=True,
                                 default=lambda self: self.env.user.company_id)
    is_all = fields.Boolean(string=u'全部员工?')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string=u'员工',
                                    domain="[('company_id', '=', company_id), ('user_id', '=', False)]")
    ttype = fields.Selection(string=u'登陆账号', selection=[('phone', '工作手机'), ('email', '工作Email')], default='phone')

    @api.onchange('is_all')
    def _onchange_is_all(self):
        for res in self:
            if res.is_all:
                domain = [
                    ('user_id', '=', False),
                    ('company_id', '=', self.env.user.company_id.id),
                    ('ding_id', '!=', False)
                ]
                emps = self.env['hr.employee'].search(domain)
                self.employee_ids = [(6, 0, emps.ids)]
            else:
                self.employee_ids = [(2, 0, self.employee_ids.ids)]

    def create_user(self):
        """
        根据员工创建系统用户
        :return:
        """
        self.ensure_one()
        company_id = self.company_id.id
        # 封装消息
        message_list = list()
        for employee in self.employee_ids:
            values = {
                'active': True,
                'company_id': company_id,
                "name": employee.name,
                'email': employee.work_email,
                'ding_user_id': employee.ding_id,
                'ding_user_phone': employee.mobile_phone,
                'employee': True,
                'employee_ids': [(6, 0, [employee.id])],
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
            message_list.append({'ding_id': employee.ding_id, 'values': values})
        return {'type': 'ir.actions.act_window_close'}


# 针对系统已存在的数据，将员工的相关用户进行匹配后关联
class EmployeeToUser(models.TransientModel):
    _name = 'dingtalk.emp.related.users'
    _description = '批量关联用户'

    company_id = fields.Many2one(comodel_name='res.company', string="选择公司", required=True,
                                 default=lambda self: self.env.user.company_id)

    def related_user(self):
        """
        自动将没有关联用户的员工通过名称进行关联
        1.获取所有相关用户（user_id）为空的员工
        2.逐个将员工名称到系统用户（res.users）中匹配
            1.若存在，则将user的id写入到员工的相关用户（user_id）中
            2.若不存在，则跳过
        :return:
        """
        self.ensure_one()
        related = self.env['dingtalk.emp.related.users']
        company_id = self.company_id
        t = threading.Thread(target=related.start_related_user, args=(company_id))
        t.start()
        return True

    @api.model
    def start_related_user(self, company):
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                employees = self.env['hr.employee'].search([('user_id', '=', False), ('company_id', '=', company.id)])
                for emp in employees:
                    user = self.env['res.users'].sudo().search([('name', '=', emp.name)], limit=1)
                    if user:
                        emp.write({'user_id': user.id})
