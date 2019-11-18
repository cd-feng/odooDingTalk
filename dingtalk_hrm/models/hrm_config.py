# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EmployeeCensusRegister(models.Model):
    _description = '户籍性质'
    _name = 'employee.census.register'

    name = fields.Char(string='名称', index=True)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', '名称不允许重复!'),
    ]
