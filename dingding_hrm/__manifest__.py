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
    'name': "钉钉集成服务-智能人事",
    'summary': """钉钉集成服务-智能人事""",
    'description': """ 智能人事相关的接口需要企业开通了钉钉官方的“智能人事”应用之后才可以调用。您可以在手机端工作台打开应用中心，搜索智能人事，然后开通应用 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'dingding_base'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/hrm_group.xml',
        'security/ir.model.access.csv',
        'data/dingding_parameter.xml',
        'views/menu.xml',
        'views/assets.xml',
        'views/employee_roster.xml',
        'views/add_employee.xml',
        'report/employee_roster.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
}
