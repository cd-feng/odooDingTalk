# -*- coding: utf-8 -*-
{
    'name': "阿里钉钉-考勤/签到记录",
    'summary': """ 支持Odoo同步阿里钉钉中所有员工考勤打卡记录、考勤结果以及签到记录 """,
    'description': """  """,
    'author': "XueFeng.Su",
    'website': "https://github.com/suxuefeng20/odooDingTalk",
    'category': '阿里钉钉/考勤',
    'version': '16.0.0',
    'license': 'LGPL-3',
    'depends': ['dingtalk2_contacts'],

    'installable': True,
    'application': False,
    'auto_install': False,

    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'datas/default_ir_cron.xml',

        'views/menu.xml',
        'views/dingtalk2_attendance_list.xml',
        'views/dingtalk2_attendance_sign.xml',

        'wizard/dingtalk2_get_attendance_list.xml',
        'wizard/dingtalk2_get_attendance_signs.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dingtalk2_attendance/static/src/js/*.js',
            'dingtalk2_attendance/static/xml/*.xml',
        ],
    }
}
