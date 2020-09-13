# -*- coding: utf-8 -*-
{
    'name': "钉钉-自动创建系统员工",
    'summary': """自动同步到员工后，根据配置是否自动创建系统用户""",
    'description': """自动同步到员工后，根据配置是否自动创建系统用户""",
    'author': "XueFeng.Su",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '1.0',
    'depends': ['dingtalk_mc'],
    'auto_install': True,
    'data': [
        'views/dingtalk_config.xml',
    ],
    'license': 'AGPL-3',
}
