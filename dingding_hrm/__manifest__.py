# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng License(GNU)
###################################################################################
{
    'name': "钉钉集成服务-智能人事",
    'summary': """钉钉集成服务-智能人事""",
    'description': """ 智能人事相关的接口需要企业开通了钉钉官方的“智能人事”应用之后才可以调用。您可以在手机端工作台打开应用中心，搜索智能人事，然后开通应用 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'dingding_base'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/dingding_parameter.xml',
        'views/menu.xml',
        'views/assets.xml',
        'views/employee_roster.xml',
        'views/add_employee.xml',
        'report/employee_roster.xml',
        'wizard/employee_roster.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
}
