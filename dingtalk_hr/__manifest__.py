# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "钉钉-HR",
    'summary': """钉钉部门、员工、角色、联系人""",
    'description': """钉钉部门、员工、角色、联系人""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'hr', 'contacts', 'dingtalk_base'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/dingtalk_security.xml',

        'wizard/change_mobile.xml',
        'wizard/synchronous.xml',

        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/res_partner.xml',
    ],
}
