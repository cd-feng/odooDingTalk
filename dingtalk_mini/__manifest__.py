# -*- coding: utf-8 -*-
{
    'name': "Odoo集成钉钉小程序",
    'summary': """odoo集成钉钉小程序""",
    'description': """odoo集成钉钉小程序""",
    'author': "ongood",
    'website': "https://www.ongood.cn",
    'category': 'dingtalk',
    'version': '13.1.2',
    'depends': ['dingtalk_mc'],
    # 'external_dependencies': {
    #     'python': ['pypinyin', 'pycryptodome', 'dingtalk-sdk'],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/dingtalk_config.xml',
        'views/web_templates.xml',
    ],
    'qweb': [
    ],
    'price': 450,
    'currency': 'EUR',
    'images': [
        'static/description/icon.png',
        'static/description/index.jpg',
    ],
    'license': 'AGPL-3',
}
