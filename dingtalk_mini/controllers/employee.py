# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import datetime
import json
import logging

import requests

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
        return json.dumps({'state': True, 'msg': '注册绑定成功！', 'employee': api_tool.create_employee_data(employee)})

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

    @http.route('/api/employee/info/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_employee_get_info(self, **kw):
        """
        通过微信openid查询员工资料
        :param kw: appid openid
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        if not params_data.get('emp_id'):
            return json.dumps({'state': False, 'msg': '参数emp_id不正确'})
        employee = request.env['hr.employee'].sudo().search([('id', '=', params_data.get('emp_id'))], limit=1)
        if not employee:
            return json.dumps({'state': False, 'msg': '账户未绑定'})
        return_data = {
            'mobile_phone': employee.mobile_phone,
            'work_phone': employee.work_phone,
            'work_email': employee.work_email,
            'number': employee.number,  # 编号
            'name': employee.name,    # 姓名
            'gender': employee.gender,  # 性别
            'education': employee.education,  # 学历
            'birthday': str(employee.birthday),  # 生日
            'marital': employee.marital,  # 婚姻状况
            'nationality': employee.nationality,  # 民族
            'birthplace': employee.birthplace,  # 籍贯
            'serve_start_date': str(employee.serve_start_date),  # 任职日期
            'company_id': employee.company_id.name,  # 公司
            'department_id': employee.department_id.name,  # 部门名称
        }
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_data})

    @http.route('/api/employee/image/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_get_employee_image(self, **kw):
        """
        返回员工的头像
        :param kw: appid openid
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        if not params_data.get('emp_id'):
            return json.dumps({'state': False, 'msg': '参数emp_id不正确'})
        employee = request.env['hr.employee'].sudo().search([('id', '=', params_data.get('emp_id'))], limit=1)
        if not employee:
            return json.dumps({'state': False, 'msg': '账户未绑定'})
        return employee.image

    @http.route('/api/employee/like/search', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def search_employee_by_like(self, **kw):
        """
        模糊搜索员工返回list(姓名、公司、部门)
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        s_data = params_data.get('searchBody')
        if not s_data:
            return json.dumps({'state': False, 'msg': '搜索内容不能为空.'})
        domain = [('name', 'like', s_data)]
        emps = request.env['hr.employee'].sudo().search(domain)
        result_list = list()
        for emp in emps:
            result_list.append({
                'res_id': emp.id,
                'wx_openid': emp.wx_openid if emp.wx_openid else 0,
                'name': emp.name,
                'company_id': emp.company_id.name,
                'department_id': emp.department_id.name,
            })
        return json.dumps({'state': True, 'msg': '查询成功', 'data': result_list})

    @http.route('/api/employee/job/getlist', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_get_all_employee_job(self, **kw):
        """
        返回所有的工作职位信息
        :param kw: appid openid
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        jobs = request.env['hr.job'].sudo().search([])
        result_list = list()
        for job in jobs:
            result_list.append(job.name)
        return json.dumps({'state': True, 'msg': '查询成功', 'data': result_list})

    @http.route('/api/wx/employee/binding/message', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def send_bangding_message_template(self, **kw):
        """
        发送绑定成功的消息通知
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        token = request.env['api.alow.access'].sudo().search([('app_id', '=', params_data.get('appid'))]).token
        url = "https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}".format(token)
        employee = request.env['hr.employee'].sudo().search([('wx_openid', '=', params_data.get('openid'))], limit=1)
        # 发送消息
        data = {
            'touser': params_data.get('openid'),
            'template_id': "Va_yl6dHQoiDJpTxQoKqT5XwQlu1MlvlTYKm40WZbQQ",  # 消息模板id
            'form_id': params_data.get('form_id'),
            'page': 'pages/index/index',
            'data': {
                "keyword1": {
                    "value": employee[0].name
                },
                "keyword2": {
                    "value": employee[0].mobile_phone
                },
                "keyword3": {
                    "value": "已绑定成功"
                }
            }
        }
        r = requests.post(url, data=json.dumps(data))
        logging.info(r.text)
        return json.dumps({'state': True, 'msg': '发送消息成功'})
