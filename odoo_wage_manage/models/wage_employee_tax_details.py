# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WageEmployeeTaxDetails(models.Model):
    _description = '个税明细'
    _name = 'wage.employee.tax.details'
    _rec_name = 'employee_id'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    start_date = fields.Date(string=u'年开始日期', required=True, index=True)
    end_date = fields.Date(string=u'年结束日期', required=True, index=True)
    year = fields.Char(string='年份', index=True)
    notes = fields.Text(string=u'备注')
    line_ids = fields.One2many('wage.employee.tax.details.line', 'cumulative_id', u'列表')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        当员工发生的变化时
        :return:
        """
        # 默认加载12个月份到列表
        for res in self:
            if len(res.line_ids) < 1:
                line_list = list()
                i = 1
                while i < 13:
                    if i < 10:
                        line_list.append((0, 0, {
                            'month': "0{}".format(str(i)),
                        }))
                    else:
                        line_list.append((0, 0, {
                            'month': str(i),
                        }))
                    i += 1
                res.line_ids = line_list

    @api.constrains('start_date', 'employee_id')
    def _constrains_start_date(self):
        for res in self:
            self.write({
                'year': str(res.start_date)[:4]
            })
            count_num = self.search_count([('employee_id', '=', res.employee_id.id), ('year', '=', str(res.start_date)[:4])])
            if count_num > 1:
                raise UserError("员工:{}已存在{}年份的员工个税明细表！请勿重复创建！".format(res.employee_id.name, str(res.start_date)[:4]))

    @api.multi
    def set_employee_tax_detail(self, month_code, line_data):
        """
        修改员工个税明细
        :return:
        """
        for line in self.line_ids:
            if line.month == month_code:
                line.sudo().write(line_data)
        return True


class WageEmployeeTaxDetailsLine(models.Model):
    _name = 'wage.employee.tax.details.line'
    _description = u"员工个税明细列表"
    _rec_name = 'cumulative_id'

    LINEMONTH = [
        ('01', '一月'),
        ('02', '二月'),
        ('03', '三月'),
        ('04', '四月'),
        ('05', '五月'),
        ('06', '六月'),
        ('07', '七月'),
        ('08', '八月'),
        ('09', '九月'),
        ('10', '十月'),
        ('11', '十一月'),
        ('12', '十二月'),
    ]
    cumulative_id = fields.Many2one(comodel_name='wage.employee.tax.details', string=u'员工个税明细')
    month = fields.Selection(string=u'月份', selection=LINEMONTH, required=True, index=True)
    taxable_salary_this_month = fields.Float(string=u'本月计税工资', digits=(10, 2))
    cumulative_tax_pay = fields.Float(string=u'累计计税工资', digits=(10, 2))
    cumulative_tax_deduction = fields.Float(string=u'累计个税抵扣', digits=(10, 2))
    accumulated_exemption = fields.Float(string=u'累计免征额', digits=(10, 2))
    cumulative_taxable_wage = fields.Float(string=u'累计应税工资', digits=(10, 2))
    tax = fields.Float(string=u'税率', digits=(10, 2))
    quick_deduction = fields.Float(string=u'速算扣除数', digits=(10, 2))
    accumulated_deductible_tax = fields.Float(string=u'累计应扣个税', digits=(10, 2))
    this_months_tax = fields.Float(string=u'本月个税', digits=(10, 2))
    cumulative_actual_tax = fields.Float(string=u'累计实际个税', digits=(10, 2))

