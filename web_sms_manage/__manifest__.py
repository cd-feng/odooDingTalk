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
    'name': "Odoo短信服务",
    'summary': """Odoo短信服务""",
    'description': """ Odoo短信服务 """,
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'sms',
    'version': '1.1',
    'depends': ['base', 'hr', 'contacts', 'auth_oauth'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'data/auth_oauth_data.xml',
        'security/odoo_sms.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/sms_config.xml',
        'views/sms_templates.xml',
        'views/sms_record.xml',

        'wizard/send_sms_message.xml',
    ]
}