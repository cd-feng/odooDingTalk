# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-待办事项管理",
    'summary': """钉钉办公-待办事项管理""",
    'description': """ 钉钉办公-待办事项管理 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin', 'mail'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'data/record_crom.xml',
        'views/work_record.xml',
    ],
}
