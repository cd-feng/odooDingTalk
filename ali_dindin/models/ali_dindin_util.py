# -*- coding: utf-8 -*-
import time
import json
import logging
import requests
import hashlib
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GetAliDinDinToken(models.TransientModel):
    _description = '获取钉钉token值'
    _name = 'ali.dindin.get.token'

    @api.model
    def get_token(self):
        """获取钉钉token值的方法函数
        获取token值需要用户用户唯一凭证（din_appkey）和用户唯一凭证密钥（din_appsecret）
        """
        din_appkey = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appkey')
        din_appsecret = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appsecret')
        if not din_appkey and not din_appsecret:
            logging.info("钉钉设置项中的AppKey和AppSecret不能为空！")
            return False
        token_url = self.env['ali.dindin.system.conf'].search([('key', '=', 'token_url')]).value
        if not token_url:
            logging.info('获取钉钉Token值URL记录不存在')
            return False
        data = {'appkey': din_appkey, 'appsecret': din_appsecret}
        # 发送数据
        result = requests.get(url=token_url, params=data, timeout=10)
        result = json.loads(result.text)
        logging.info(">>>获取钉钉token结果:{}".format(result))
        if result.get('errcode') == 0:
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')])
            if token:
                token.write({
                    'value': result.get('access_token')
                })
        else:
            logging.info(">>>获取钉钉Token失败！请检查网络是否通畅或检查日志输出")
