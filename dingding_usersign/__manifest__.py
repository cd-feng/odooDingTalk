# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-用户签到记录",
    'summary': """钉钉办公-用户签到记录""",
    'description': """ 钉钉办公-用户签到记录 """,
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
        'views/department_sign.xml',
        'views/users_sign.xml',
        'views/sign_list.xml',
    ],
    'images':  ['static/description/app1.png']
}
