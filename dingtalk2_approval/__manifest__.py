# -*- coding: utf-8 -*-
{
    'name': "阿里钉钉-审批工作流",
    'summary': """用于支持钉钉审批工作流相关功能""",
    'description': """可实现将odoo中单据推送至钉钉进行审批，并结合钉钉回调回写审批结果""",
    'author': "XueFeng.Su",
    'website': "https://github.com/suxuefeng20/odooDingTalk",
    'category': '阿里钉钉/审批',
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

        'views/menu.xml',
        'views/approval_template.xml',
        'views/dingtalk_approval_log.xml',
        'views/approval_model_button.xml',
        'views/approval_control.xml',

        'wizard/approval_template.xml',
        'wizard/return_approval_state.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dingtalk2_approval/static/xml/*.xml',
            'dingtalk2_approval/static/src/js/approval_template.js',
        ]
    },
}
