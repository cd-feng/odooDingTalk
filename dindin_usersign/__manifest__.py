# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-用户签到记录",
    'summary': """钉钉办公-用户签到记录""",
    'description': """ 钉钉办公-用户签到记录 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'views/department_sign.xml',
        'views/users_sign.xml',
        'views/sign_list.xml',
    ],
    'price': '50',
    'currency': 'EUR',
    'images':  ['static/description/app1.png']
}
