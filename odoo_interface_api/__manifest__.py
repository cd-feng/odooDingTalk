# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng  License-Apache
###################################################################################
{
    'name': "Odoo外部接口api",
    'summary': """提供外部系统访问Odoo系统时的通道，比如基础数据（系统用户、员工、部门、公司等）模块所有传递格式为json""",
    'description': """提供外部系统访问Odoo系统时的通道，比如基础数据（系统用户、员工、部门、公司等）模块所有传递格式为json""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'api',
    'version': '1.0',
    'depends': ['base', 'hr', 'mail', 'hr_attendance'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/assets.xml',
        'views/alow_access_api.xml',
        'views/hr_employee.xml',
        'views/applet_configs.xml',
    ],
}
