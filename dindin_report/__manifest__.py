# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-日志",
    'summary': """钉钉办公-日志""",
    'description': """ 钉钉办公-日志 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'security/dindin_security.xml',
        'data/system_conf.xml',
        'views/report_template.xml',
        'views/report.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
}
