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
    'name': "钉钉集成服务-考勤拓展模块",
    'summary': """钉钉集成服务-考勤拓展模块，为了不影响基于dingding——base模块的考勤功能，将所有需要依赖odoo原生的模块的功能移动至本模块，可通过设置中选择进行安装""",
    'description': """钉钉集成服务-考勤拓展模块，为了不影响基于dingding——base模块的考勤功能，将所有需要依赖odoo原生的模块的功能移动至本模块，可通过设置中选择进行安装""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['dingding_attendance', 'hr_attendance'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'views/asset.xml',
        'views/hr_attendance.xml',
    ],
}
