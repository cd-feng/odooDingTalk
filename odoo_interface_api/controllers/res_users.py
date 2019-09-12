# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import json
import logging
from odoo import http, _
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.http import request
from . import api_tool
_logger = logging.getLogger(__name__)


class ResUserAPI(Home, http.Controller):

    @http.route('/api/wx/users/password/update', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_wx_users_update_pwd(self, **kw):
        """
        修改用户密码： 需要先检查员工对应的系统用户，存在系统用户时才允许修改密码
        :param kw:（openid appid password
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        openid = params_data.get('openid')
        password = params_data.get('password')
        if not openid or not password:
            return json.dumps({'state': False, 'msg': '参数不正确'})
        # 查询是否已绑定员工
        employee = request.env['hr.employee'].sudo().search([('wx_openid', '=', openid)])
        if not employee:
            return json.dumps({'state': False, 'msg': '未绑定员工，不需要修改密码！'})
        if not employee.user_id:
            return json.dumps({'state': False, 'msg': '员工没有关联登录系统的用户账户，不需要修改密码操作！'})
        employee.user_id.sudo().write({
            'password': password
        })
        return json.dumps({'state': True, 'msg': '新的密码已生效！'})

