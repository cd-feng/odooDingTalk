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
    'name': "钉钉审批-出货报告",
    'summary': """钉钉审批-出货报告""",
    'description': """钉钉审批-出货报告""",
    'author': "SuXueFeng",
    'category': 'dingding',
    'version': '1.0',
    'depends': ['oa_base', 'fleet'],
    'installable': True,
    'auto_install': True,
    'data': [
        'groups/group.xml',
        'security/ir.model.access.csv',
        'data/defaulr_num.xml',
        'data/default_data.xml',

        'views/transfer_application.xml',
        'views/resignation_application.xml',
        'views/vehicle_application.xml',
        'views/itemuse_application.xml',
        'views/seal_application.xml',
        'views/general_application.xml',
    ],
}
