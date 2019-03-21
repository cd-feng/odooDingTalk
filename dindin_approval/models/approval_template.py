# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinApprovalTemplate(models.Model):
    _name = 'dindin.approval.template'
    _description = "审批模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    process_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_template(self):
        """获取审批模板"""
        logging.info(">>>获取审批模板...")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'process_listbyuserid')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'offset': 0,
            'size': 100,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=20)
            result = json.loads(result.text)
            # logging.info(">>>获取审批模板返回结果{}".format(result))
            if result.get('errcode') == 0:
                d_res = result.get('result')
                for process in d_res.get('process_list'):
                    data = {
                        'name': process.get('name'),
                        'icon_url': process.get('icon_url'),
                        'process_code': process.get('process_code'),
                        'url': process.get('url'),
                    }
                    template = self.env['dindin.approval.template'].search(
                        [('process_code', '=', process.get('process_code'))])
                    if template:
                        template.write(data)
                    else:
                        self.env['dindin.approval.template'].create(data)
            else:
                raise UserError('获取审批模板失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取审批模板结束...")
