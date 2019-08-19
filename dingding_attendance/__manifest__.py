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
    'name': "钉钉集成服务-考勤",
    'summary': """钉钉集成服务-考勤""",
    'description': """ 钉钉集成服务-考勤 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['base', 'dingding_base', 'hr_attendance'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'security/dingding_security.xml',
        'data/dingding_parameter.xml',
        'views/asset.xml',
        'views/menu.xml',
        'views/simplegroups.xml',
        'views/hr_dingding_plan.xml',
        'views/hr_leaves_list.xml',
        'views/hr_attendance_result.xml',
        'views/hr_attendance_record.xml',
        'views/hr_attendance.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
