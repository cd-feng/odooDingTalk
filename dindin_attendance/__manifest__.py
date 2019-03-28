# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-考勤排班详情",
    'summary': """钉钉办公-考勤排班详情""",
    'description': """ 钉钉办公-考勤排班详情 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dindin',
    'version': '1.0',
    'depends': ['base', 'ali_dindin', 'mail'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'views/asset.xml',
        'views/simplegroups.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
