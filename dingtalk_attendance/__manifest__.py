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
        'security/ir.model.access.csv',

        'views/assets.xml',
        'views/user_sign_list.xml',
        'views/simplegroups.xml',
        'views/dingtalk_plan.xml',
        'views/attendance_record.xml',
        'views/attendance_result.xml',
        'views/leaves_list.xml',
        'views/res_config_settings_views.xml',

        'wizard/simplegroups.xml',
        'wizard/dingtalk_plan.xml',
        'wizard/attendance_record.xml',
        'wizard/attendance_result.xml',
        'wizard/leaves_list.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]
}
