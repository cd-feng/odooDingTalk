# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng  License-Apache
###################################################################################
{
    'name': "微信小程序HCM系统",
    'summary': """向指定的微信小程序提供odoo服务""",
    'description': """向指定的微信小程序提供odoo服务""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'api',
    'version': '1.0',
    'depends': ['base', 'hr', 'mail', 'hr_attendance'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',

        'views/assets.xml',
        'views/user_checkin.xml',
        'views/alow_access_api.xml',
        'views/hr_employee.xml',
        'views/applet_configs.xml',
        'views/user_location.xml',

        'wizard/user_location.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]
}
