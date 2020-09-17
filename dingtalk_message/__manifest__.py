# -*- coding: utf-8 -*-
{
    'name': "钉钉消息功能模块",
    'summary': """自定义配置钉钉消息""",
    'description': """消息通知""",
    'author': "XueFeng.Su",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0.1.0.1',
    'depends': ['dingtalk_mc'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/default_message_config.xml',
        'views/dingtalk_msg_config.xml',
    ],
}
