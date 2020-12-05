# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import base64
import json
import datetime
import logging
import time
from odoo import http, _
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.http import request
from . import api_tool
_logger = logging.getLogger(__name__)


class UserCheckAPI(Home, http.Controller):

    @http.route('/api/user/location/check/in', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_user_location_check_in(self, **kw):
        """
        用户正常签到
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        # 获取表单参数
        openid = params_data.get('openid')
        employee = api_tool.get_employee_by_wx_openid(openid)
        if not employee:
            return json.dumps({'state': False, 'msg': '员工不存在！'})
        # 签到时间
        checkin_time = params_data.get('checkin_time')
        if not checkin_time:
            return json.dumps({'state': False, 'msg': '签到时间不存在！'})
        checkin_time = self._get_time_stamp(checkin_time)
        # 签到地点
        location = params_data.get('location')
        request.env['hcm.user.checkin'].sudo().create({
            'emp_id': employee.id,
            'check_time': checkin_time,
            'check_type': 'normal',
            'location': location,
        })
        return json.dumps({'state': True, 'msg': '签到成功!'})

    @http.route('/api/user/location/check/field/in', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_user_location_check_field_in(self, **kw):
        """
        用户外勤打卡
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        # 获取表单参数
        openid = params_data.get('openid')
        employee = api_tool.get_employee_by_wx_openid(openid)
        if not employee:
            return json.dumps({'state': False, 'msg': '员工不存在！'})
        # 签到时间
        checkin_time = params_data.get('checkin_time')
        if not checkin_time:
            return json.dumps({'state': False, 'msg': '签到时间不存在！'})
        checkin_time = self._get_time_stamp(checkin_time)
        # 签到地点
        location = params_data.get('location')
        # 签到描述
        description = params_data.get('description')
        # 创建打卡记录
        user_check = request.env['hcm.user.checkin'].sudo().create({
            'emp_id': employee.id,
            'check_time': checkin_time,
            'check_type': 'field',
            'location': location,
            'description': description,
        })
        # 图片
        images = params_data.get('images')
        request.env['ir.attachment'].sudo().create({
            'name': images.filename,
            'datas_fname': images.filename,
            'datas': base64.b64encode(images.read()),
            'res_id': user_check.id,
            'res_model': 'hcm.user.checkin',
        })
        return json.dumps({'state': True, 'msg': '外勤打卡成功!'})

    @http.route('/api/user/check/date/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def get_user_checkin_info(self, **kw):
        """
        根据日期和员工获取打卡详情
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
        check_date = params_data.get('check_date')
        if not check_date or check_date[-2:] == '-0':
            return json.dumps({'state': False, 'msg': '查询日期格式不正确。'})
        checkins = request.env['hcm.user.checkin'].sudo().search([('emp_id', '=', employee.id), ('check_date', '=', check_date)])
        return_list = list()
        for checkin in checkins:
            check_time = datetime.datetime.strftime(checkin.check_time + datetime.timedelta(hours=8), "%Y-%m-%d %H:%M:%S")
            return_list.append({
                'signDate': check_time,
                'signTime': check_time[10:],
                'timeType': checkin.time_type,
                'location': checkin.location,
                'checkType': checkin.check_type,
            })
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_list})

    @http.route('/api/user/location/get/list', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def get_user_location_list(self, **kw):
        """
        返回员工的考勤点list
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
        # 获取员工考勤点
        e_location = request.env['hcm.employee.location'].sudo().search([('emp_id', '=', employee.id)], limit=1)
        if not e_location:
            return json.dumps({'state': False, 'msg': '员工未配置考勤点，请联系管理员添加。'})
        result_list = list()
        for location in e_location.location_ids:
            result_list.append({
                'deviation': location.deviation,   # 允许误差(米)
                'address': location.location_id.address,   # 详细地址
                'latitude': location.location_id.latitude,   # 纬度
                'longitude': location.location_id.longitude,   # 经度
            })
        return json.dumps({'state': True, 'msg': '查询成功', 'data': result_list})

    def _get_time_stamp(self, time_num):
        """
        将13位时间戳转换为时间(utc=0)
        :param time_num:
        :return: "%Y-%m-%d %H:%M:%S"
        """
        time_stamp = float(time_num) / 1000
        time_array = time.gmtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)