# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "Authing",
    'summary': """集成Authing登录""",
    'description': """ 集成Authing登录 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'authing',
    'version': '12.0.1',
    'depends': ['base', 'auth_oauth'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        # 'data/auth_oauth.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/res_users.xml',
        'views/new_user_groups.xml',
    ],
    'images': ['static/description/images1.png','static/description/images2.png','static/description/images3.png']
}
