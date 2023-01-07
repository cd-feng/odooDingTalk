# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ding_id = fields.Char(string='钉钉ID', index=True)
    ding_unionid = fields.Char(string='Union标识', index=True)
    ding_avatar = fields.Char(string="钉钉头像地址")
    ding_job_number = fields.Char(string='员工工号', tracking=True)
    ding_org_email = fields.Char(string='钉钉企业邮箱', tracking=True)
    ding_work_place = fields.Char(string='办公地点', tracking=True)
    ding_hired_date = fields.Date(string='入职时间', tracking=True)
    ding_is_active = fields.Boolean("是否激活了钉钉", default=False)
    ding_is_admin = fields.Boolean("是否为企业的管理员", default=False)
    ding_is_boss = fields.Boolean("是否为企业的老板", default=False)
    ding_is_leader = fields.Boolean("是否是部门的主管", default=False)
    department_ids = fields.Many2many('hr.department', 'ding_employee_and_department_rel', string='所属部门')

    @api.model
    def processing_dingtalk_result(self, data, company_id):
        """
        处理钉钉请求后的数据，封装为odoo员工格式，用于创建或修改
        """
        value = {
            'company_id': company_id,
            'name': data.get('name'),  # 员工名称
            'ding_id': data.get('userid'),  # 钉钉用户Id
            'ding_unionid': data.get('unionid'),  # 钉钉唯一标识
            'ding_avatar': data.get('avatar') or False,  # 头像URL地址
            'mobile_phone': data.get('mobile'),  # 手机号
            'work_phone': data.get('telephone'),  # 办公电话
            'ding_job_number': data.get('job_number'),  # 工号
            'job_title': data.get('title'),  # 职位
            'work_email': data.get('email'),  # email
            'ding_org_email': data.get('org_email'),  # 员工的企业邮箱
            'ding_work_place': data.get('work_place'),  # 员工的办公地点
            'ding_is_active': data.get('active'),
            'ding_is_admin': data.get('admin'),
            'ding_is_boss': data.get('boss'),
            'ding_is_leader': data.get('leader'),
        }
        # 支持显示国际手机号
        if data.get('state_code') != '86':
            value.update({'mobile_phone': '+{}-{}'.format(data.get('stateCode'), data.get('mobile'))})
        if data.get('hired_date'):
            value['ding_hired_date'] = dt.timestamp_to_local_date(self, data.get('hiredDate'))
        if data.get('dept_id_list'):
            dept_ids = self.env['hr.department'].search([
                ('ding_id', 'in', data.get('dept_id_list')), ('company_id', '=', company_id)])
            value.update({
                'department_ids': [(6, 0, dept_ids.ids)],
                'department_id': dept_ids[0].id or False,
            })
        return value

