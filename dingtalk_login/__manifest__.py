# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "钉钉-Login",
    'summary': """Login：使用钉钉账号登录odoo系统；密码、扫码以及钉钉端应用免登功能""",
    'description': """Login：使用钉钉账号登录odoo系统；密码、扫码以及钉钉端应用免登功能""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '12.0',
    'depends': ['base', 'dingtalk_hr', 'auth_oauth'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'data/auth_oauth_data.xml',
        'views/res_users_views.xml',
        'views/login_templates.xml',
    ],
}
