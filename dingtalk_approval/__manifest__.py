# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "钉钉-审批引擎",
    'summary': """基于钉钉审批功能将odoo指定单据推送到钉钉进行审批""",
    'description': """基于钉钉审批功能将odoo指定单据推送到钉钉进行审批""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'dingtalk_callback'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/dingtalk_security.xml',
        'security/ir.model.access.csv',

        'wizard/dingtalk_template.xml',

        'views/assets.xml',
        'views/dingtalk_template.xml',
        'views/approval_control.xml',
    ],
    "qweb": [
        "static/xml/*.xml"
    ],
}

