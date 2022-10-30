# -*- coding: utf-8 -*-
{
    'name': "阿里钉钉集成-Base",
    'summary': """ 基础工具模块 """,
    'description': """ 基础工具模块 """,
    'author': "XueFeng.Su",
    'website': "https://github.com/suxuefeng20/odooDingTalk",
    'category': '阿里钉钉/Base',
    'version': '16.0.0',
    'license': 'LGPL-3',
    'depends': ['base'],

    'installable': True,
    'application': True,
    'auto_install': False,

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/menu.xml',
        'views/dingtalk2_config.xml',

    ],
    'assets': {
        'web.assets_backend': [],
    }
}
