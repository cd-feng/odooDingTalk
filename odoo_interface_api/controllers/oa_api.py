# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import datetime
import json
import logging
from odoo import http, _
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.http import request
from . import api_tool
_logger = logging.getLogger(__name__)


class OaApi(Home, http.Controller):

    @http.route('/api/oa/transfer/create', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_oa_create_transfer(self, **kw):
        """
        创建转正申请表单
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        # 获取表单参数
        openid = params_data.get('openid')
        employee = api_tool.get_employee_by_wx_openid(openid)
        job = request.env['hr.job'].sudo().search([('name', '=', params_data.get('job_id'))], limit=1)
        data = {
            'originator_user_id': employee.id,
            'emp_id': employee.id,
            'entry_date': params_data.get('entry_date'),
            'transfer_date': params_data.get('transfer_date'),
            'job_id': job.id if job else False,
            'job_num': params_data.get('job_num'),
            'post_understanding': params_data.get('post_understanding'),
            'sum_up': params_data.get('sum_up'),
            'opinion_text': params_data.get('opinion_text'),
        }
        request.env['oa.transfer.application'].sudo().create(data)
        return json.dumps({'state': True, 'msg': '写入成功'})

    @http.route('/api/oa/transfer/red/openid', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_oa_read_transfer_by_openid(self, **kw):
        """
        根据员工读取转正申请单
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
            return json.dumps({'state': False, 'msg': '员工不存在'})
        transfers = request.env['oa.transfer.application'].sudo().search([('originator_user_id', '=', employee.id)])
        return_list = list()
        for transfer in transfers:
            return_list.append({
                'res_id': transfer.id,
                'name': "%s-%s" % (transfer.process_code, transfer.emp_id.name),
            })
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_list})

    @http.route('/api/oa/transfer/red/info', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def api_oa_read_transfer_by_id(self, **kw):
        """
        读取转正详情
        :param kw:
        :return:
        """
        params_data = request.params.copy()
        if not api_tool.check_api_access(params_data.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        # 获取表单参数
        res_id = params_data.get('res_id')
        transfer = request.env['oa.transfer.application'].sudo().search([('id', '=', res_id)], limit=1)
        return_data = {
            'employee_name': transfer.originator_user_id.name,
            'entry_date': str(transfer.entry_date),
            'transfer_date': str(transfer.transfer_date),
            'job_id': transfer.job_id.name,
            'job_num': transfer.job_num,
            'post_understanding': transfer.post_understanding,
            'sum_up': transfer.sum_up,
            'opinion_text': transfer.opinion_text,
        }
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_data})
