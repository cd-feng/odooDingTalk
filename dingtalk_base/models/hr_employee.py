# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    OfficeStatus = [
        ('2', '试用期'), ('3', '正式'), ('5', '待离职'), ('-1', '无状态')
    ]

    ding_id = fields.Char(string='钉钉Id', index=True)
    din_unionid = fields.Char(string='Union标识', index=True)
    din_jobnumber = fields.Char(string='员工工号')
    ding_avatar_url = fields.Char('头像url')
    hired_date = fields.Date(string='入职时间')
    din_isAdmin = fields.Boolean("是管理员", default=False)
    din_isBoss = fields.Boolean("是老板", default=False)
    din_isLeader = fields.Boolean("是部门主管", default=False)
    din_isHide = fields.Boolean("隐藏手机号", default=False)
    din_isSenior = fields.Boolean("高管模式", default=False)
    din_active = fields.Boolean("是否激活", default=True)
    real_authed = fields.Boolean("是否已实名认证")
    din_orderInDepts = fields.Char("所在部门序位")
    din_isLeaderInDepts = fields.Char("是否为部门主管")
    work_status = fields.Selection(string=u'入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')], default='2')
    office_status = fields.Selection(string=u'在职子状态', selection=OfficeStatus, default='-1')
    department_ids = fields.Many2many('hr.department', 'emp_dept_dingtalk_rel', string='所属部门')

    @api.model
    def add_dingtalk_employee(self, user_ids, company):
        """
        获取用户详情执行函数
        :return:
        """
        config = self.env['dingtalk.config'].sudo().search([('company_id', '=', company.id)], limit=1)
        employee_list = list()
        for user_id in user_ids:
            try:
                client = dt.get_client(self, dt.get_dingtalk_config(self, company))
                req_result = client.post('topapi/v2/user/get', {
                    'userid': user_id,
                })
            except Exception as e:
                _logger.info("获取用户详情失败：{}".format(e))
                continue
            if req_result.get('errcode') == 0:
                result = req_result.get('result')
                data = {
                    'name': result.get('name'),  # 员工名称
                    'ding_id': result.get('userid'),  # 钉钉用户Id
                    'din_unionid': result.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': result.get('mobile'),  # 手机号
                    'work_phone': result.get('telephone'),  # 分机号
                    'work_location': result.get('work_place'),  # 办公地址
                    'notes': result.get('remark'),  # 备注
                    'job_title': result.get('title'),  # 职位
                    'work_email': result.get('email'),  # email
                    'din_jobnumber': result.get('job_number'),  # 工号
                    'din_isSenior': result.get('senior'),  # 高管？
                    'din_isAdmin': result.get('admin'),  # 是管理员
                    'din_isBoss': result.get('boss'),  # 是老板
                    'din_isHide': result.get('hide_mobile'),  # 隐藏手机号
                    'din_active': result.get('active'),  # 是否激活
                    'company_id': company.id,
                    'ding_avatar_url': result.get('avatar'),   # 头像
                    'real_authed': result.get('real_authed'),   # 是否已完成实名认证
                }
                if result.get('hired_date'):
                    date_str = dt.timestamp_to_local_date(self, result.get('hired_date'))
                    data.update({'hired_date': date_str})
                if result.get('dept_id_list'):
                    dep_ding_ids = result.get('dept_id_list')
                    dep_list = self.env['hr.department'].sudo().search([
                        ('ding_id', 'in', dep_ding_ids), ('company_id', '=', company.id)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)], 'department_id': dep_list[0].id if dep_list else False})
                employee = self.env['hr.employee'].sudo().search([('ding_id', '=', user_id), ('company_id', '=', company.id)])
                if not employee:
                    employee = self.env['hr.employee'].sudo().create(data)
                else:
                    employee.write(data)
                employee_list.append(employee)
            else:
                _logger.info("从钉钉同步员工时发生意外，原因:{}".format(req_result.get('errmsg')))
        self._cr.commit()
        if config.is_auto_create_user:   # 自动创建系统用户?
            return self.create_employee_user(employee_list, company)

    @api.model
    def create_employee_user(self, employee_list, company):
        """
        :param employee_list: 员工
        :param company: 公司
        :return:
        """
        for employee in employee_list:
            if employee.user_id:
                continue
            domain = ['|', ('login', '=', employee.work_email), ('login', '=', employee.mobile_phone)]
            user = self.env['res.users'].sudo().search(domain, limit=1)
            if user and not user.employee_id:
                employee.write({'user_id': user.id})
            else:
                if employee.work_email:
                    login = employee.work_email
                elif employee.mobile_phone:
                    login = employee.mobile_phone
                else:
                    continue
                values = {
                    'login': login,
                    'password': login,
                    'active': True,
                    'company_id': company.id,
                    "name": employee.name,
                    'email': employee.work_email,
                    'oauth_uid': employee.ding_id,
                    'employee': True,
                    'employee_id': employee.id,
                    'employee_ids': [(6, 0, [employee.id])],
                }
                name_count = self.env['res.users'].sudo().search_count([('name', 'like', employee.name)])
                if name_count > 0:
                    user_name = employee.name + str(name_count + 1)
                    values['name'] = user_name
                try:
                    user = self.env['res.users'].sudo().create(values)
                except Exception:
                    continue
                employee.write({'user_id': user.id})

    @api.constrains('ding_id')
    def _constrains_ding_id(self):
        """
        检查是否重复
        :return:
        """
        for res in self:
            if res.ding_id:
                result_count = self.search_count([('ding_id', '=', res.ding_id), ('company_id', '=', res.company_id.id)])
                if result_count > 1:
                    raise exceptions.ValidationError("钉钉ID已存在，员工：{}".format(res.name))

    @api.model
    def modify_dingtalk_employee(self, user_ids, company_id):
        """
        当钉钉员工发生了变化时，需要从钉钉中读取最新的数据
        :return:
        """
        for user_id in user_ids:
            employee = self.env['hr.employee'].sudo().search([('ding_id', '=', user_id), ('company_id', '=', company_id.id)])
            if not employee:
                return
            try:
                client = dt.get_client(self, dt.get_dingtalk_config(self, company_id))
                req_result = client.post('topapi/v2/user/get', {
                    'userid': user_id,
                })
            except Exception as e:
                _logger.info("获取用户详情失败：{}".format(e))
                continue
            if req_result.get('errcode') == 0:
                result = req_result.get('result')
                data = {
                    'name': result.get('name'),  # 员工名称
                    'ding_id': result.get('userid'),  # 钉钉用户Id
                    'din_unionid': result.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': result.get('mobile'),  # 手机号
                    'work_phone': result.get('telephone'),  # 分机号
                    'work_location': result.get('work_place'),  # 办公地址
                    'notes': result.get('remark'),  # 备注
                    'job_title': result.get('title'),  # 职位
                    'work_email': result.get('email'),  # email
                    'din_jobnumber': result.get('job_number'),  # 工号
                    'din_isSenior': result.get('senior'),  # 高管？
                    'din_isAdmin': result.get('admin'),  # 是管理员
                    'din_isBoss': result.get('boss'),  # 是老板
                    'din_isHide': result.get('hide_mobile'),  # 隐藏手机号
                    'din_active': result.get('active'),  # 是否激活
                    'company_id': company_id.id,
                    'ding_avatar_url': result.get('avatar'),  # 头像
                    'real_authed': result.get('real_authed'),  # 是否已完成实名认证
                }
                if result.get('hired_date'):
                    date_str = dt.timestamp_to_local_date(self, result.get('hired_date'))
                    data.update({'hired_date': date_str})
                if result.get('dept_id_list'):
                    dep_ding_ids = result.get('dept_id_list')
                    dep_list = self.env['hr.department'].sudo().search([
                        ('ding_id', 'in', dep_ding_ids), ('company_id', '=', company_id.id)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)],
                                 'department_id': dep_list[0].id if dep_list else False})
                employee.write(data)
            else:
                _logger.info("从钉钉同步员工时发生意外，原因:{}".format(req_result.get('errmsg')))

