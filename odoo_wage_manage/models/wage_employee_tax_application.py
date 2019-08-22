# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WageEmployeeTaxInformation(models.Model):
    _description = '纳税信息'
    _name = 'wage.tax.information'
    _rec_name = 'employee_id'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    CERTIFICATESTATUS = [
        ('00', '居民身份证'),
        ('01', '护照'),
        ('02', '其他个人证件'),
    ]

    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    year = fields.Integer(string=u'扣除年度', required=True, index=True)
    name = fields.Char(string='姓名', required=True, index=True)
    certificate_type = fields.Selection(string=u'证件类型', selection=CERTIFICATESTATUS, default='00')
    certificate_number = fields.Char(string='证件号码', required=True)
    phone = fields.Char(string='手机号', required=True)
    addr = fields.Char(string='联系地址')
    email = fields.Char(string='电子邮箱')
    company_id = fields.Many2one(comodel_name='res.company', string=u'工作单位', required=True)
    spouse_situation = fields.Selection(string=u'配偶情况', selection=[('00', '有配偶'), ('01', '无配偶')], default='01')
    spouse_name = fields.Char(string='配偶姓名')
    spouse_certificate_type = fields.Selection(string=u'配偶证件类型', selection=CERTIFICATESTATUS, default='00')
    spouse_certificate_number = fields.Char(string='配偶证件号码')
    notes = fields.Text(string=u'备注')


class WageEmployeeTaxChildEducationApplication(models.Model):
    _description = '子女教育专项扣除申请'
    _name = 'wage.tax.child.education.application'
    _rec_name = 'tax_id'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tax_id = fields.Many2one(comodel_name='wage.tax.information', string=u'纳税人', required=True, index=True)
    line_ids = fields.One2many('wage.tax.child.education.application.line', 'education_id', string=u'子女信息')
    notes = fields.Text(string=u'备注')


class WageEmployeeTaxChildEducationApplicationLine(models.Model):
    _description = '子女教育专项扣除申请列表'
    _name = 'wage.tax.child.education.application.line'
    _rec_name = 'name'

    @api.model
    def _get_default_country_id(self):
        return self.env['res.company']._company_default_get('payment.transaction').country_id.id

    EDUCATIONSTATUS = [
        ('00', '学前教育阶段'),
        ('01', '义务教育'),
        ('02', '高中阶段教育'),
        ('03', '高等教育'),
    ]

    education_id = fields.Many2one(comodel_name='wage.tax.child.education.application', string=u'子女教育专项扣除')
    name = fields.Char(string='子女姓名', required=True)
    certificate_number = fields.Char(string='证件号码', required=True)
    birth_date = fields.Date(string='出生日期', required=True)
    country_id = fields.Many2one(comodel_name='res.country', string=u'国家(地区)', default=_get_default_country_id)
    education_stage = fields.Selection(string=u'当前受教育阶段', selection=EDUCATIONSTATUS, default='00')
    
    education_phase_start_time = fields.Date(string=u'当前受教育阶段起始时间')
    education_phase_end_time = fields.Date(string=u'当前受教育阶段结束时间')
    education_termination_time = fields.Date(string=u'教育终止时间')

    now_country_id = fields.Many2one(comodel_name='res.country', string=u'当前就读国家', default=_get_default_country_id)
    school_name = fields.Char(string='当前就读学校名称', required=True)
    deduction_ratio = fields.Selection(string=u'本人扣除比例', selection=[('100', '100%'), ('50', '50%'), ],
                                       default='100', required=True)
    
