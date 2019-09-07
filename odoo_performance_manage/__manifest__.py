# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
{
    'name': "Odoo绩效管理",
    'summary': """统一管理员工绩效""",
    'description': """统一管理员工绩效""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'performance',
    'version': '1.0',
    'depends': ['base', 'hr', 'mail'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/default_num.xml',

        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/performance_grade.xml',
        'views/evaluation_groups.xml',
        'views/dimension_manage.xml',
        'views/indicator_library.xml',
        'views/performance_assessment.xml',

        'wizard/initiate_performance.xml',
    ],
}
