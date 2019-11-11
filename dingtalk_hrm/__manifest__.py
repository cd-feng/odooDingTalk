# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng License(GNU)
###################################################################################
{
    'name': "钉钉-智能人事",
    'summary': """钉钉-智能人事""",
    'description': """ 智能人事相关的接口需要企业开通了钉钉官方的“智能人事”应用之后才可以调用。您可以在手机端工作台打开应用中心，搜索智能人事，然后开通应用 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'dingtalk_hr'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/dingtalk_security.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/employee_roster.xml',
        'views/add_employee.xml',
        'views/hrm_dimission_list.xml',

        'report/employee_roster.xml',

        'wizard/employee_roster.xml',
        'wizard/hrm_dimission_list.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
}
