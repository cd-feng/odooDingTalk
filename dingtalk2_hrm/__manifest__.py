# -*- coding: utf-8 -*-
{
    'name': "钉钉集成-智能人事",
    'summary': """用于支持钉钉智能人事相关功能""",
    'description': """用于支持钉钉智能人事相关功能""",
    'author': "XueFeng.Su",
    'website': "https://github.com/suxuefeng20/odooDingTalk",
    'category': '阿里钉钉/智能人事',
    'version': '16.0.0',
    'license': 'LGPL-3',
    'depends': ['dingtalk2_contacts'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        # 'datas/ir_cron.xml',

        'views/menu.xml',
        'views/dingtalk_config.xml',
        'views/employee_roster.xml',

        'wizard/employee_roster_list.xml',
        'wizard/addpreentry.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dingtalk2_hrm/static/src/xml/templates.xml',
            'dingtalk2_hrm/static/src/js/employee_roster.js',
        ]
    }
}
