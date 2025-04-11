# -*- coding: utf-8 -*-
{
    'name': "Odoo-钉钉",
    'summary': """本模块支持从钉钉中同步联系人数据""",
    'description': """ """,
    'author': "XueFeng.Su",
    'website': "https://github.com/cd-feng",
    'category': 'Dingtalk/HR',
    'version': '18.0.0.1',
    'depends': ['hr'],
    "license": "AGPL-3",
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/default_ir_cron.xml',

        'views/menu.xml',
        'views/dingtalk_setting.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/res_users.xml',

        'wizard/hr_department_wizard.xml',
        'wizard/hr_employee_wizard.xml',
    ],
    'images': [
        'static/description/image_1.png',
    ],
}
