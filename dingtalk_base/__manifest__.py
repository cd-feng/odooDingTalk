# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################
{
    'name': "钉钉-Base",
    'summary': """钉钉基础模块：钉钉各项参数设置以及模块工具""",
    'description': """钉钉基础模块：钉钉各项参数设置以及模块工具""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'web_progress'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/dingtalk_security.xml',
        'views/res_config_settings_views.xml',
    ],
}
