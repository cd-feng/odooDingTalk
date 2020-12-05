# -*- coding: utf-8 -*-
import json
from requests import ReadTimeout
from odoo.exceptions import UserError
from odoo import models, fields, api
import requests


class HCMAttendanceLocation(models.Model):
    _name = "hcm.attendance.location"
    _rec_name = 'name'
    _description = "考勤点管理"
    _order = 'id'

    active = fields.Boolean(string=u'active', default=True)
    name = fields.Char(string='考勤点描述', required=True)
    location_id = fields.Many2one(comodel_name='hcm.location.manage', string=u'考勤位置', required=True)
    deviation = fields.Integer(string='允许误差(米)', default=200)
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)
    manage_user_id = fields.Many2one(comodel_name='hr.employee', string=u'管理员')


class HCMLocationManage(models.Model):
    _name = "hcm.location.manage"
    _rec_name = 'address'
    _description = "考勤位置"
    _order = 'id'

    sequence = fields.Integer(string='序号')
    adcode = fields.Char(string='编码')
    province = fields.Char(string='省份', required=True)
    city = fields.Char(string='城市', required=True)
    district = fields.Char(string='地区')
    address = fields.Char(string='详细地址')
    category = fields.Char(string='类别')
    latitude = fields.Char(string='纬度', required=True)
    longitude = fields.Char(string='经度', required=True)


class EmployeeLocationManage(models.Model):
    _name = "hcm.employee.location"
    _rec_name = 'emp_id'
    _description = "员工考勤点管理"
    _order = 'id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True)
    job_id = fields.Many2one(comodel_name='hr.job', string=u'工作岗位')
    location_ids = fields.Many2many('hcm.attendance.location', string=u'员工考勤点')

    @api.onchange('emp_id')
    @api.constrains('emp_id')
    def _update_emp_id(self):
        for res in self:
            if res.emp_id:
                # 检查是否重复
                contract_count = self.search_count([('emp_id', '=', res.emp_id.id)])
                if contract_count > 1:
                    raise UserWarning("员工:{}已存在考勤点，请勿重复创建！".format(res.emp_id.name))
                res.department_id = res.emp_id.department_id.id if res.emp_id.department_id else False
                res.job_id = res.emp_id.job_id.id if res.emp_id.job_id else False
