# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-消息管理",
    'summary': """钉钉办公-消息管理""",
    'description': """ 钉钉办公-消息管理 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin', 'mail'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'data/config.xml',
        'views/config.xml',
        'views/work_message.xml',
        # 'views/department.xml',
        # 'views/employee.xml',
        # 'views/extcontact.xml',
    ],
    # 'qweb': [
    #     'static/xml/*.xml'
    # ]

}
