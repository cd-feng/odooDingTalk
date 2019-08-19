# -*- coding: utf-8 -*-
{
    'name': "钉钉集成服务-消息管理",
    'summary': """钉钉集成服务-消息管理""",
    'description': """ 钉钉集成服务-消息管理 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'dingding_base'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'data/config.xml',
        'views/config.xml',
        'views/assets.xml',
        'views/work_message.xml',
        'views/dingding_chat.xml',
        'views/mail_message.xml',
        'views/ding_robot.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
    'images':  ['static/description/msg4.png', 'static/description/msg3.png', 'static/description/msg2.png']
}
