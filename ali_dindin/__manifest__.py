# -*- coding: utf-8 -*-
{
    'name': "阿里-钉钉办公集成",
    'summary': """阿里-钉钉办公集成""",
    'description': """ 阿里-钉钉办公集成 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.1',
    'depends': ['base', 'hr', 'contacts'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'security/dindin_security.xml',
        'data/system_conf.xml',
        'views/menu.xml',
        'views/systemc_conf.xml',
        'views/res_config_settings_views.xml',
        'views/asset.xml',
        'views/department.xml',
        'views/employee.xml',
        'views/extcontact.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ]
}
