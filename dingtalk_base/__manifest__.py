# -*- coding: utf-8 -*-
{
    'name': "钉钉集成-基础应用",
    'summary': """基础模块，用于同步基础数据、回调等""",
    'description': """基础模块，用于同步基础数据、回调等""",
    'author': "XueFeng.Su",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '14.1.1',
    'license': 'OPL-1',
    'depends': ['base', 'hr', 'mail', 'web_notify'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'data/default_callback_list.xml',

        'views/menu.xml',
        'views/dingtalk_config.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/res_partner.xml',
        'views/callback_manage.xml',
        'views/dingtalk_callback_log.xml',

        'wizard/synchronous_department.xml',
        'wizard/synchronous_employee.xml',
        'wizard/synchronous_partner.xml',
        'wizard/update_employee_avatar.xml',
        'wizard/dingtalk_callback_get.xml',
    ],

    'assets': {
        'web.assets_qweb': [
            'dingtalk_base/static/xml/*.xml',
        ],
        'web.assets_backend': [
            'dingtalk_base/static/src/js/callback_manage.js',
        ],
    }
}
