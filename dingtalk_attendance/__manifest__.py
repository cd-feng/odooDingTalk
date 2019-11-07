# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "钉钉-考勤",
    'summary': """考勤：同步钉钉端的考勤、签到记录到odoo系统中""",
    'description': """考勤：同步钉钉端的考勤、签到记录到odoo系统中""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'dingtalk_hr', 'hr_attendance'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        # 'data/auth_oauth_data.xml',
        # 'views/res_users_views.xml',
        # 'views/login_templates.xml',
    ],
}
