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
    'name': "Odoo外部接口api",
    'summary': """提供外部系统访问Odoo系统时的通道，比如基础数据（系统用户、员工、部门、公司等）模块所有传递格式为json""",
    'description': """提供外部系统访问Odoo系统时的通道，比如基础数据（系统用户、员工、部门、公司等）模块所有传递格式为json""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'api',
    'version': '1.0',
    'depends': ['base', 'hr', 'mail'],
    'installable': False,
    'application': False,
    'auto_install': False,
    'data': [

    ],
}
