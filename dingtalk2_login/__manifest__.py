# -*- coding: utf-8 -*-
{
    'name': "阿里钉钉-扫码/账号登录(钉钉身份验证)",
    'summary': """ 支持钉钉扫码、账号密码登录到odoo系统 """,
    'description': """  """,
    'author': "XueFeng.Su",
    'website': "https://github.com/suxuefeng20/odooDingTalk",
    'category': '阿里钉钉/身份验证',
    'version': '16.0.0',
    'license': 'LGPL-3',
    'depends': ['dingtalk2_contacts', 'auth_oauth'],

    'installable': True,
    'application': False,
    'auto_install': False,

    'data': [
        'data/auth_oauth_data.xml',

        'views/dingtalk2_config.xml',
    ],
    'assets': {
        'web.assets_backend': [

        ],
    }
}
