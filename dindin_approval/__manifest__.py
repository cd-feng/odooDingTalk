# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-审批模板",
    'summary': """钉钉办公-审批模板""",
    'description': """ 钉钉办公-审批模板 """,
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
        'data/mail_channel.xml',
        'views/asset.xml',
        'views/approval_template.xml',
        'views/approval_control.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
    'price': '50',
    'currency': 'EUR',
    'images':  ['static/description/app1.png', 'static/description/app2.png']
}
