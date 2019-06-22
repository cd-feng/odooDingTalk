# -*- coding: utf-8 -*-
{
    'name': "钉钉办公-运动",
    'summary': """钉钉办公-运动""",
    'description': """企业使用此接口可查询用户是否启用了钉钉运动，如果未开启，不会参与企业的钉钉运动排名""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['base', 'ali_dindin'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/health_group.xml',
        'security/ir.model.access.csv',
        'data/system_conf.xml',
        'views/menu.xml',
        'views/res_config_settings.xml',
        'views/employee.xml',
        'views/department.xml',
        'views/dingding_health.xml',
    ],
}
