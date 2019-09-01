# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
{
    'name': "Odoo薪酬/工资管理",
    'summary': """员工社保、薪资计算、薪资档案，部分功能需配合钉钉模块和钉钉审批模块""",
    'description': """员工社保、薪资计算、薪资档案，部分功能需配合钉钉模块和钉钉审批模块""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'wage',
    'version': '1.0',
    'depends': ['base', 'web_progress', 'hr', 'mail'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/default_num.xml',
        'views/asset.xml',
        'views/wage_insured_scheme.xml',
        'views/wage_insured_scheme_employee.xml',
        'views/wage_insured_monthly_statement.xml',
        'views/wage_structure.xml',
        'views/wage_archives.xml',
        'views/wage_calculate_salary_rules.xml',
        'views/wage_special_additional_deduction.xml',
        'views/wage_statistics_annal.xml',
        'views/wage_payroll_accounting.xml',
        'views/wage_employee_tax_details.xml',
        'views/wage_employee_tax_application.xml',
        'views/odoo_wage_payslip.xml',

        'wizard/wage_insured_monthly_statement.xml',
        'wizard/wage_archives.xml',
        'wizard/wage_payroll_accounting.xml',
        'wizard/wage_employee_tax_details.xml',
        'wizard/wage_statistics_annal.xml',

    ],
    'qweb': [
        'static/xml/*.xml'
    ]
}
