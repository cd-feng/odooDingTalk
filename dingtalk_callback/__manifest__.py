# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "钉钉-回调管理",
    'summary': """回调管理：注册钉钉业务事件回调至odoo系统""",
    'description': """回调管理：注册钉钉业务事件回调至odoo系统，比如通讯录发生改变时，实时同步到odoo系统""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'dingtalk_hr'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/dingtalk_security.xml',
        'security/ir.model.access.csv',
        'data/callback_list.xml',

        'views/assets.xml',
        'views/callback_manage.xml',
        'wizard/callback_get.xml',
    ],
    "qweb": [
        "static/xml/*.xml"
    ],
}
