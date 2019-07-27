# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-回调管理",
    'summary': """钉钉办公-回调管理""",
    'description': """ 钉钉办公-回调管理 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'dingding_base'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'data/call_back.xml',
        'views/call_back_list.xml',
        'views/call_back.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ],
    'images':  ['static/description/app1.png', 'static/description/app2.png']
}
