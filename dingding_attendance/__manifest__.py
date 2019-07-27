# -*- coding: utf-8 -*-
{
    'name': "钉钉集成服务-考勤",
    'summary': """钉钉集成服务-考勤""",
    'description': """ 钉钉集成服务-考勤 """,
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
        'security/dingding_security.xml',
        'data/dingding_parameter.xml',
        'views/asset.xml',
        'views/menu.xml',
        'views/simplegroups.xml',
        'views/hr_dingding_plan.xml',
        'views/hr_leaves_list.xml',
        'views/hr_attendance.xml',
        'views/hr_attendance_record.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
