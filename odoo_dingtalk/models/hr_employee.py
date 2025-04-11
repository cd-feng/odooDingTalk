# -*- coding: utf-8 -*-
import logging
import base64
import requests
from ..tools.dingtalk_hr import DingTalkHr
from odoo import api, fields, models, exceptions

_logger = logging.getLogger(__name__)

def get_emp_avatar(avatar_url, timeout=5):
    """
    下载员工的头像
    """
    try:
        return base64.b64encode(requests.get(avatar_url, timeout=timeout).content)
    except Exception:
        return False


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    job_number = fields.Char(string="员工工号", index=True)
    dingtalk_id = fields.Char(string='钉钉用户ID', index=True)
    dingtalk_avatar_url = fields.Char('钉钉头像URL链接')
    dingtalk_department_ids = fields.Many2many('hr.department', 'hr_employee_and_wechat_department_rel', string='钉钉部门列表')
    dingtalk_active = fields.Boolean(string='激活状态')
    dingtalk_admin = fields.Boolean(string='是否为企业管理员')
    dingtalk_boss = fields.Boolean(string='是否为企业的老板')
    dingtalk_leader = fields.Boolean(string='是否是部门的主管')
    dingtalk_exclusive_account = fields.Boolean(string='是否专属帐号')

    @api.model
    def request_dingtalk_employee_data(self, company_id):
        conf_id = self.env['dingtalk.setting'].sudo().get_setting_param(company_id)
        if not conf_id:
            raise exceptions.UserError("请先配置钉钉应用API参数！")
        try:
            client = DingTalkHr(app_key=conf_id.app_key, app_secret=conf_id.app_secret)
            for dept_id in self.env['hr.department'].search([('company_id', '=', company_id), ('dingtalk_id', '!=', False)]):
                _logger.info(f"开始同步从钉钉中同步[{dept_id.name}]的员工数据...")
                data = client.get_user_list(dept_id=dept_id.dingtalk_id)
                if data:
                    self.update_department_emp_list(data, company_id)
        except Exception as e:
            raise e

    def update_department_emp_list(self, employee_list, company_id):
        """
        更新部门下的所有员工
        """
        if not employee_list:
            _logger.warning("未收到任何员工数据，跳过同步...")
            return
        employee_model, department_model = self.env['hr.employee'], self.env['hr.department']
        employee_dict = dict(employee_model.search([('company_id', '=', company_id)]).mapped(lambda e: (e.dingtalk_id, e.id)))
        department_dict = dict(department_model.search([('company_id', '=', company_id)]).mapped(lambda d: (d.dingtalk_id, d.id)))
        new_emp_values, updated_emp_ids = [], []
        # 处理员工数据（新增/更新）
        for data in employee_list:
            # _logger.info(f"处理钉钉员工数据：{data}")
            dingtalk_id, name, position = data['userid'], data['name'], data.get('title', '')
            # 处理部门
            dept_id_list = data.get('dept_id_list', [])
            department_id = False
            dingtalk_department_ids = []
            if dept_id_list:
                main_department = dept_id_list[0]
                department_id = department_dict.get(main_department)
                dingtalk_department_ids = [department_dict.get(x) for x in dept_id_list]
            values = {
                'company_id': company_id,
                'name': name,
                'dingtalk_id': dingtalk_id,
                'job_title': position,
                'job_number': data.get('job_number'),
                'department_id': department_id,
                'work_email': data.get('email', data.get('org_email')),
                'work_phone': data.get('telephone'),
                'mobile_phone': data.get('mobile'),
                'dingtalk_avatar_url': data.get('avatar'),
                'dingtalk_active': data.get('active'),
                'dingtalk_admin': data.get('admin'),
                'dingtalk_boss': data.get('boss'),
                'dingtalk_leader': data.get('leader'),
                'dingtalk_exclusive_account': data.get('exclusive_account'),
                'dingtalk_department_ids': [(6, 0, dingtalk_department_ids)]
            }
            if dingtalk_id in employee_dict:      # 需要更新的员工
                updated_emp_ids.append((employee_dict[dingtalk_id], values))
            else:                                 # 需要批量创建的新员工
                new_emp_values.append(values)
        if updated_emp_ids:
            for emp_id, values in updated_emp_ids:
                employee_model.browse(emp_id).write(values)
        if new_emp_values:
            employee_model.create(new_emp_values)
        self.env.cr.commit()
        _logger.info(f"钉钉员工同步完成，共更新 {len(updated_emp_ids)} 条，新增 {len(new_emp_values)} 条.")

    def create_employee_user(self, company_id):
        """
        创建用户
        """
        with self.pool.cursor() as new_cr:
            self = self.with_env(self.env(cr=new_cr, su=True))
            conf_id = self.env['dingtalk.setting'].sudo().get_setting_param(company_id)
            if conf_id.is_create_dingtalk_user and conf_id.dingtalk_default_passwd:
                self.create_res_users(company_id, conf_id.dingtalk_default_passwd)
                self.env.cr.commit()
            if conf_id.is_get_emp_avatar:
                self.get_emp_dingtalk_avatar(company_id)

    def get_emp_dingtalk_avatar(self, company_id):
        """
        将钉钉头像设置为员工的头像
        """
        update_data = {}
        employees = self.search([('company_id', '=', company_id), ('dingtalk_avatar_url', '!=', False)])
        for emp in employees:
            _logger.info(f"获取 {emp.name} 员工的头像。")
            try:
                emp_avatar = get_emp_avatar(emp.dingtalk_avatar_url)
                update_data[emp.id] = {'image_1920': emp_avatar}
            except Exception as e:
                _logger.warning(f"处理 {emp.name} 的头像时发生错误: {e}")
        # 批量写入头像数据
        if update_data:
            for emp_id, data in update_data.items():
                self.browse(emp_id).write(data)
            _logger.info(f"成功批量更新 {len(update_data)} 位员工的头像。")
        else:
            _logger.info(f"没有需要更新头像的员工。")

    @api.model
    def create_res_users(self, company_id, default_password):
        """
        为指定公司(company_id)下的所有员工创建 Odoo 登录用户。
        规则：
        1. 只为 `user_id` 为空的员工创建用户
        2. 使用 `work_phone` 作为 `login`
        3. 设定默认密码
        4. 绑定 `employee_id`
        """
        res_user, hr_employee = self.env['res.users'], self.env['hr.employee']
        # 获取所有没有创建用户的员工
        employees = hr_employee.search([('company_id', '=', company_id), ('user_id', '=', False), ('mobile_phone', '!=', False)])
        if not employees:
            _logger.info(f"没有需要创建用户的员工")
            return
        _logger.info(f"发现{len(employees)}名员工需要创建用户")
        existing_users = res_user.search_read([], ['id', 'login'])
        existing_logins = {user['login'] for user in existing_users}
        new_users = []
        for emp in employees:
            if emp.mobile_phone in existing_logins:
                _logger.warning(f"用户 {emp.mobile_phone} 已存在，跳过")
                continue
            new_users.append({
                'name': emp.name,
                'login': emp.mobile_phone,
                'dingtalk_user_id': emp.dingtalk_id,
                'password': default_password,
                'company_id': company_id,
                'employee_id': emp.id,                  # 绑定 employee_id
                'employee_ids': [(6, 0, [emp.id])],     # 反向绑定 employees
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]  # 赋予普通用户权限
            })
        if new_users:
            created_users = res_user.create(new_users)
            # 绑定 user_id 到员工表
            # for emp, user in zip(employees, created_users):
            #     emp.user_id = user.id
            _logger.info(f"成功创建 {len(created_users)} 名新用户")

