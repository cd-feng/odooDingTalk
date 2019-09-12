# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
import requests
from odoo.http import Controller, route, json, request
from . import api_tool

logger = logging.getLogger(__name__)


class WeiXinApiInterface(Controller):
    """微信api接口"""

    @route('/api/wx/openid/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def wx_get_openid(self, **kw):
        """
        用appid和secret到微信api中换取微信用户openid
        :param kw:
        :return: openid
        """
        wx_code = request.params['usercode']
        app_id = request.params['appid']
        secret = request.params['secret']
        if not wx_code or not app_id or not secret:
            return False
        if not api_tool.check_api_access(app_id):
            return False
        url = "https://api.weixin.qq.com/sns/jscode2session?"
        new_url = "{}appid={}&secret={}&js_code={}&grant_type=authorization_code".format(url, app_id, secret, wx_code)
        result = requests.get(url=new_url, timeout=5)
        result = json.loads(result.text)
        return result['openid']

    @route('/api/wx/employee/check/openid', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def wx_check_employee_openid(self, **kw):
        """
        根据微信openid查询员工是否存在
        :param kw:
        :return:
        """
        app_id = request.params['appid']
        openid = request.params['openid']
        if not openid:
            return json.dumps({'state': False, 'msg': '未检测到openid参数'})
        if not api_tool.check_api_access(app_id):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        employee = request.env['hr.employee'].sudo().search([('wx_openid', '=', openid)])
        if not employee:
            return json.dumps({'state': False, 'msg': '未绑定员工'})
        return json.dumps({'state': True, 'msg': '已绑定员工'})

    @route('/api/wx/openid/get_and_check', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def wx_get_openid_and_check_openid(self, **kw):
        """
        用appid和secret到微信api中换取微信用户openid,然后在系统中查看是否已绑定员工，返回查询绑定的结果和openid
        :param kw:
        :return:
        """
        params = request.params.copy()
        wx_code = params.get('usercode')
        app_id = params.get('appid')
        secret = params.get('secret')
        if not wx_code or not app_id or not secret:
            return json.dumps({'state': False, 'msg': '参数不正确'})
        if not api_tool.check_api_access(app_id):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        url = "https://api.weixin.qq.com/sns/jscode2session?"
        new_url = "{}appid={}&secret={}&js_code={}&grant_type=authorization_code".format(url, app_id, secret, wx_code)
        result = requests.get(url=new_url, timeout=5)
        result = json.loads(result.text)
        employee_num = request.env['hr.employee'].sudo().search_count([('wx_openid', '=', result['openid'])])
        if employee_num < 1:
            return json.dumps({'state': False, 'msg': '未绑定员工', 'openid': result['openid']})
        return json.dumps({'state': True, 'msg': '已绑定员工', 'openid': result['openid']})

# # 获取微信access_token值 该值有效期为2小时，超过时间需要重新获取
# @route('/wx/access_token', type='http', auth='public', methods=['get', 'post'], csrf=False)
# def wx_access_token(self, **kw):
# 	url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&"
# 	newurl = ('%s%s%s%s%s' % (url, 'appid=', kw['appid'], '&secret=', kw['secret']))
# 	logger.info(newurl)
# 	response = urllib2.urlopen(newurl)
# 	data = response.read()
# 	logger.info(data)
# 	return data
