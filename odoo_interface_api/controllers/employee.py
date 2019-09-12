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


class EmployeeAPI(Home, http.Controller):

    @http.route('/api/wx/employee/binding/account', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_wx_employee_bingding_account(self, **kw):
        """
        绑定员工
        :param kw:（员工姓名emp_name、工作emial work_email、 办公手机 mobile_phone  /appid）
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        emp_name = params_data.get('emp_name')
        work_email = params_data.get('work_email')
        mobile_phone = params_data.get('mobile_phone')
        openid = params_data.get('openid')
        wx_nick_name = params_data.get('nick_name')
        wx_avatar_url = params_data.get('avatar_url')
        if not emp_name or not work_email or not mobile_phone or not openid:
            return json.dumps({'state': False, 'msg': '参数不正确'})
        # 查询是否已绑定
        employee_num = request.env['hr.employee'].sudo().search_count([('wx_openid', '=', openid)])
        if employee_num >= 1:
            return json.dumps({'state': False, 'msg': '已绑定员工，如需重新绑定请先解除绑定！'})
        # 查询员工
        domain = [('name', '=', emp_name), ('work_email', '=', work_email), ('mobile_phone', '=', mobile_phone)]
        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            return json.dumps({'state': False, 'msg': '没有在系统中找到对应的员工，请检查信息是否正确！'})
        employee.sudo().write({
            'wx_openid': openid,
            'wx_nick_name': wx_nick_name,
            'wx_avatar_url': wx_avatar_url,
        })
        employee.sudo().message_post(body=u"账号已绑定外部系统，Code: %s！" % params_data.get('appid'), message_type='notification')
        return json.dumps({'state': True, 'msg': '注册绑定成功！'})

    @http.route('/api/wx/employee/binding/clear', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_wx_employee_bingding_clear(self, **kw):
        """
        解除账号绑定
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        openid = params_data.get('openid')
        if not openid:
            return json.dumps({'state': False, 'msg': '参数不正确'})
        # 查询是否已绑定
        employee = request.env['hr.employee'].sudo().search([('wx_openid', '=', openid)])
        if not employee:
            return json.dumps({'state': False, 'msg': '没有查询到已绑定的员工！'})
        employee.sudo().write({
            'wx_openid': "",
            'wx_nick_name': "",
            'wx_avatar_url': "",
        })
        employee.sudo().message_post(body=u"账号已解除外部系统的绑定，Code: %s！" % params_data.get('appid'), message_type='notification')
        return json.dumps({'state': True, 'msg': '已解除账号绑定！'})

    @http.route('/api/wx/employee/info/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_wx_employee_get_info(self, **kw):
        """
        通过微信openid查询员工资料
        :param kw: appid openid
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        if not params_data.get('openid'):
            return json.dumps({'state': False, 'msg': '参数openid不正确'})
        employee = request.env['hr.employee'].sudo().search([('wx_openid', '=', params_data.get('openid'))], limit=1)
        if not employee:
            return json.dumps({'state': False, 'msg': '账户未绑定'})
        return_data = {
            'employee': {
                'name': employee.name,
                'phone': employee.mobile_phone,
                'email': employee.work_email,
                'number': employee.id,
                'job': employee.job_id.name if employee.job_id else "",
            },
            'dept': {
                'name': employee.department_id.name if employee.department_id else "暂无部门数据",
                'manage_name': employee.department_id.manager_id.name if employee.department_id and employee.department_id.manager_id else "暂无部门经理"
            }
        }
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_data})
