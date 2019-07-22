# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-扫码/免密登录模块",
    'summary': """钉钉办公-扫码/免密登录模块""",
    'description': """ 钉钉办公-扫码/免密登录模块 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'mail', 'auth_oauth', 'ali_dindin', 'dindin_message'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'data/system_conf.xml',
        'data/auth_oauth_data.xml',
        'views/auto_templates.xml',
    ],
}
