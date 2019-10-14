# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import logging
import requests
from odoo.http import Controller, route, json, request
from . import api_tool

logger = logging.getLogger(__name__)


class AppletApiController(Controller):
    """小程序接口"""

    @route('/api/applet/home_image/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def get_applet_hemo_images(self, **kw):
        """
        获取小程序首页滚动图片  返回所有状态为有效的图片地址
        :param kw:
        :return:
        """
        params = request.params.copy()
        if not api_tool.check_api_access(params.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        images = request.env['applet.home.images'].sudo().search([('active', '=', True)])
        return_list = list()
        for image in images:
            return_list.append({
                'name': image.name,
                'url': image.url,
                'type': image.ttype,
            })
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_list})

    @route('/api/applet/enterprise_dynamic/get', type='http', auth='none', methods=['get', 'post'], csrf=False)
    def get_all_enterprise_dynamic(self, **kw):
        """
        获取企业动态数据 返回所有有效的数据
        :param kw:
        :return:
        """
        params = request.params.copy()
        if not api_tool.check_api_access(params.get('appid')):
            return json.dumps({'state': False, 'msg': '拒绝访问'})
        dynamics = request.env['applet.enterprise.dynamic'].sudo().search([('active', '=', True)])
        return_list = list()
        for dynamic in dynamics:
            tag_list = list()
            for tag in dynamic.tag_ids:
                tag_list.append(tag.name)
            return_list.append({
                'res_id': dynamic.id,
                'name': dynamic.name,
                'body': dynamic.body,
                'tags': tag_list,
                'image': dynamic.image,
            })
        return json.dumps({'state': True, 'msg': '查询成功', 'data': return_list})

