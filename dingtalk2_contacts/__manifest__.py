# -*- coding: utf-8 -*-
{
    'name': "阿里钉钉-通讯录管理",
    'summary': """ 支持Odoo同步阿里钉钉中的企业、部门、员工、外部联系人等信息 """,
    'description': """ 支持Odoo同步阿里钉钉中的企业、部门、员工、外部联系人等信息 """,
    'author': "XueFeng.Su",
    'website': "https://github.com/suxuefeng20/odooDingTalk",
    'category': '阿里钉钉/通讯录',
    'version': '16.0.0',
    'license': 'LGPL-3',
    'depends': ['hr', 'contacts', 'dingtalk2_base'],

    'installable': True,
    'application': False,
    'auto_install': False,

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/menu.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',

        'wizard/hr_department.xml',
        'wizard/hr_employee.xml',
        'wizard/res_partner.xml',
    ],
    'assets': {
        'web.assets_backend': [

        ],
    }
}
