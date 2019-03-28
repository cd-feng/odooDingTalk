# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-日程",
    'summary': """钉钉办公-日程""",
    'description': """ 钉钉办公-日程 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dindin',
    'version': '1.0',
    'depends': ['base', 'ali_dindin', 'calendar'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        # 'security/ir.model.access.csv',
        'data/system_conf.xml',
        'data/defaulr_num.xml',
        'views/calendar.xml',
    ],

}
