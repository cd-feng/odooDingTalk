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
    'name': "钉钉审批-出勤休假",
    'summary': """钉钉审批-出勤休假""",
    'description': """钉钉审批-出勤休假""",
    'author': "SuXueFeng",
    'category': 'dingding',
    'installable': True,
    'version': '1.0',
    'depends': ['oa_base'],
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/leave_type.xml',
        'data/defaulr_num.xml',
        'views/config.xml',
        'views/leave_application.xml',
        'views/travel_application.xml',
        'views/outing_application.xml',
        'views/overtime_application.xml',
        'views/reissue_application.xml',
    ],
}
