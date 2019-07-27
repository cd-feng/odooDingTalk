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

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    agent_id = fields.Char(string=u'AgentId')
    corp_id = fields.Char(string=u'企业CorpId')
    app_key = fields.Char(string=u'AppKey')
    app_secret = fields.Char(string=u'AppSecret')
    token = fields.Boolean(string="自动获取Token")
    din_delete_extcontact = fields.Boolean(string=u'删除外部联系人')
    din_create_employee = fields.Boolean(string=u'添加员工')
    din_update_employee = fields.Boolean(string=u'修改员工')
    din_delete_employee = fields.Boolean(string=u'删除员工')
    din_create_department = fields.Boolean(string=u'添加部门')
    din_update_department = fields.Boolean(string=u'修改部门')
    din_delete_department = fields.Boolean(string=u'删除部门')
    din_login_appid = fields.Char(string=u'钉钉登录appId')
    din_login_appsecret = fields.Char(string=u'钉钉登录appSecret')

    # 安装钉钉模块
    # module_dingding_attendance = fields.Boolean('钉钉办公-考勤')
    # module_dingding_calendar = fields.Boolean('钉钉办公-日程')
    # module_dingding_approval = fields.Boolean('钉钉办公-审批')
    # module_dingding_callback = fields.Boolean('钉钉办公-回调管理')
    # module_dingding_hrm = fields.Boolean('钉钉办公-智能人事')
    # module_dingding_message = fields.Boolean('钉钉办公-消息管理')
    # module_dingding_report = fields.Boolean('钉钉办公-日志')
    # module_dingding_usersign = fields.Boolean('钉钉办公-签到')
    # module_dingding_workrecord = fields.Boolean('钉钉办公-待办事项')
    # module_dingding_health = fields.Boolean('钉钉办公-运动')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            agent_id=self.env['ir.config_parameter'].sudo().get_param('dingding_base.agent_id'),
            corp_id=self.env['ir.config_parameter'].sudo().get_param('dingding_base.corp_id'),
            app_key=self.env['ir.config_parameter'].sudo().get_param('dingding_base.app_key'),
            app_secret=self.env['ir.config_parameter'].sudo().get_param('dingding_base.app_secret'),
            token=self.env['ir.config_parameter'].sudo().get_param('dingding_base.token'),
            din_delete_extcontact=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_delete_extcontact'),
            din_create_employee=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_create_employee'),
            din_update_employee=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_update_employee'),
            din_delete_employee=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_delete_employee'),
            din_create_department=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_create_department'),
            din_update_department=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_update_department'),
            din_delete_department=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_delete_department'),
            din_login_appid=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_login_appid'),
            din_login_appsecret=self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_login_appsecret'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.agent_id', self.agent_id)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.corp_id', self.corp_id)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.app_key', self.app_key)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.app_secret', self.app_secret)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.token', self.token)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_delete_extcontact', self.din_delete_extcontact)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_create_employee', self.din_create_employee)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_update_employee', self.din_update_employee)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_delete_employee', self.din_delete_employee)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_create_department', self.din_create_department)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_update_department', self.din_update_department)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_delete_department', self.din_delete_department)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_login_appid', self.din_login_appid)
        self.env['ir.config_parameter'].sudo().set_param('dingding_base.din_login_appsecret', self.din_login_appsecret)

    def getting_token(self):
        self.env.ref('dingding_base.ir_cron_data_get_token').method_direct_trigger()
