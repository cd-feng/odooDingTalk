# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-概览",
    'summary': """钉钉办公-概览""",
    'description': """ 钉钉办公-概览 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin', 'dindin_workrecord', 'dindin_approval'],
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
