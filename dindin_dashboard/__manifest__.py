# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-仪表盘",
    'summary': """钉钉办公-仪表盘""",
    'description': """ 钉钉办公-仪表盘 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dindin',
    'version': '1.0',
    'depends': ['base', 'ali_dindin'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'data/system_conf.xml',
        'views/dashboard.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
