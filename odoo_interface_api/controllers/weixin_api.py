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
        employee = request.env['hr.employee'].sudo().search([('wx_openid', '=', result['openid'])], limit=1)
        if not employee:
            return json.dumps({'state': False, 'msg': '未绑定员工', 'openid': result['openid']})
        employee_data = api_tool.create_employee_data(employee)
        return json.dumps({'state': True, 'msg': '已绑定员工', 'openid': result['openid'], 'employee': employee_data})

    @route('/api/wx/post/message', type='json', auth='none', methods=['get', 'post'], csrf=False)
    def get_wx_post_message(self, **kw):
        """
        接受微信端用户发给小程序的消息以及开发者需要的事件推送
        :param kw:
        :return:
        """
        logging.info("-----微信推送消息-------")
        json_str = request.jsonrequest
        logging.info(json_str)
        logging.info("-----json-str-end-------")
        params = request.params.copy()
        logging.info(params)
        # token = "odoohcmtoken"
        # EncodingAESKey = "ddbmDYeaW4OUERHWGspWwgOZq62VZdROP0NyVY7idT3"
