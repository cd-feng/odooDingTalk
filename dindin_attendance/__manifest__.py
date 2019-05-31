# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-考勤排班详情",
    'summary': """钉钉办公-考勤排班详情""",
    'description': """ 钉钉办公-考勤排班详情 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin', 'mail', 'hr_attendance'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'security/dingding_security.xml',
        'data/system_conf.xml',
        'views/asset.xml',
        'views/simplegroups.xml',
        # 'views/attendance_list.xml',
        'views/hr_attendance.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
