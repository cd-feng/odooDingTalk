# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GetUserLocation(models.TransientModel):
    _name = 'get.user.location.tran'
    _description = "获取位置信息"

    name = fields.Char(string='详细地址')
    area = fields.Char(string='地区')

    def get_location(self):
        """
        获取位置信息
        :return:
        """
        self.ensure_one()
        # 获取腾讯地图配置
        qqmap = self.env['hcm.qq.map'].search([('active', '=', True)], limit=1)
        if not qqmap:
            raise UserError("请先配置一条可用的腾讯地图信息！")
        url = "https://apis.map.qq.com/ws/place/v1/search"
        data = {
            'keyword': self.name,
            'boundary': "region({},0)".format(self.area),
            'key': qqmap.key,
            'page_size': 10,
            'output': 'json',
        }
        try:
            result = requests.get(url=url, params=data, timeout=5)
            result = json.loads(result.text)
            if result.get('status') == 0:
                for d_res in result['data']:
                    data = {
                        'address': d_res.get('address'),
                        'category': d_res.get('category'),
                    }
                    location = d_res.get('location')
                    data.update({
                        'latitude': location.get('lat'),
                        'longitude': location.get('lng'),
                    })
                    ad_info = d_res.get('ad_info')
                    data.update({
                        'adcode': ad_info.get('adcode'),
                        'province': ad_info.get('province'),
                        'city': ad_info.get('city'),
                        'district': ad_info.get('district'),
                    })
                    locations = self.env['hcm.location.manage'].search([('address', '=', data.get('address'))])
                    if locations:
                        locations.write(data)
                    else:
                        self.env['hcm.location.manage'].create(data)
            else:
                raise UserError("提示：{}".format(result.get('message')))
        except ReadTimeout:
            raise UserError("连接腾讯位置服务'WebService'超时！")
        return {'type': 'ir.actions.act_window_close'}

