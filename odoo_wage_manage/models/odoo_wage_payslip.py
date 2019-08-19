# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WageEmployeePayslip(models.Model):
    _description = '工资条'
    _name = 'odoo.wage.payslip'
    _rec_name = 'name'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    name = fields.Char(string='Name', default='New')
    active = fields.Boolean(string=u'Active', default=True)
    company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, track_visibility='onchange')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True)
    job_id = fields.Many2one(comodel_name='hr.job', string=u'岗位')
    emp_number = fields.Char(string='员工号')
    start_date = fields.Date(string=u'所属期起', required=True, index=True, track_visibility='onchange')
    end_date = fields.Date(string=u'所属期止', required=True, index=True, track_visibility='onchange')
    date_code = fields.Char(string='期间', index=True, required=True, track_visibility='onchange')

    base_wage = fields.Float(string=u'基本工资', digits=(10, 2))
    structure_wage = fields.Float(string=u'项目加项', digits=(10, 2))
    absence_sum = fields.Float(string=u'缺勤扣款合计', digits=(10, 2))
    performance_sum = fields.Float(string=u'绩效合计', digits=(10, 2))
    overtime_sum = fields.Float(string=u'加班费合计', digits=(10, 2))
    attendance_sum = fields.Float(string=u'打卡扣款合计', digits=(10, 2))

    personal_social_security = fields.Float(string=u'个人社保', digits=(10, 2))
    personal_provident_fund = fields.Float(string=u'个人公积金', digits=(10, 2))

    taxable_income = fields.Float(string=u'个税', digits=(10, 2))

    pay_wage = fields.Float(string=u'应发工资', digits=(10, 2))
    real_wage = fields.Float(string=u'实发工资', digits=(10, 2))
    notes = fields.Text(string=u'备注')

    @api.constrains('employee_id', 'date_code')
    def _constrains_employee_alter_name(self):
        """
        设置name字段
        :return:
        """
        for res in self:
            res.write({
                'job_id': res.employee_id.job_id.id,
                'name': "{}<{}>工资条".format(res.employee_id.name, res.date_code),
                'emp_number': res.employee_id.din_jobnumber,
            })


