# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': "钉钉集成服务",
    'summary': """基础数据同步、参数配置、扫码登录、免密登录""",
    'description': """基础数据同步、参数配置、扫码登录、免密登录""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'hr', 'contacts', 'auth_oauth', 'mail'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'uninstall_hook': 'uninstall_hook',
    'data': [
        'security/ir.model.access.csv',
        'security/dingding_security.xml',
        'data/dingding_parameter.xml',
        'data/auth_oauth_data.xml',
        'data/dingding_callback_list.xml',

        'views/menu.xml',
        'views/res_users_views.xml',
        'wizard/synchronous.xml',
        'wizard/change_mobile.xml',
        'views/web_widget.xml',
        'views/dingding_parameter.xml',
        'views/res_config_settings_views.xml',
        'views/hr_department.xml',
        'views/hr_employee.xml',
        'views/res_partner.xml',
        'views/login_templates.xml',
        'views/dingding_callback_list.xml',
        'views/dingding_callback_manage.xml',
        'views/dingding_approval_template.xml',
        'views/dingding_approval_control.xml',
    ],
    "qweb": [
        "static/xml/*.xml"
    ],
    'images': ['static/description/index2.png','static/description/index1.png']
}
