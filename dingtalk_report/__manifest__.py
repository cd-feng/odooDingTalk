# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng  GNU
###################################################################################

{
    'name': "钉钉-日志",
    'summary': """员工日报、周报、月报等""",
    'description': """员工日报、周报、月报等""",
    'author': "Su-XueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingtalk',
    'version': '13.0',
    'depends': ['base', 'dingtalk_hr'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/dingtalk_security.xml',
        'security/ir.model.access.csv',

        'data/report_category_data.xml',
        'data/ir_rule.xml',

        'views/assets.xml',
        'views/report_category.xml',
        'views/report_report.xml',
        'views/report_template.xml',

        'wizard/dingtalk_report_template.xml',
        'wizard/dingtalk_report_list.xml',
    ],
    "qweb": [
        "static/xml/*.xml"
    ],
}
