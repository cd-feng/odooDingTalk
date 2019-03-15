# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

""" 钉钉部门功能模块 """


# 拓展部门
class HrDepartment(models.Model):
    _inherit = 'hr.department'

    din_id = fields.Char(string='钉钉Id')


# 同步钉钉部门功能模型
class DinDinSynchronousDepartment(models.TransientModel):
    _name = 'dindin.synchronous.department'
    _description = "同步钉钉部门功能模型"

    @api.multi
    def start_synchronous_department(self):
        logging.info(">>>同步钉钉部门列表")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'department_list')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'id': 1,
        }
        result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
        logging.info(">>>获取钉钉部门结果:{}".format(result.text))
        result = json.loads(result.text)
        if result.get('errcode') == 0:
            for res in result.get('department'):
                data = {
                    'name': res.get('name'),
                    'din_id': res.get('id'),
                }
                if res.get('parentid') != 1:
                    partner_department = self.env['hr.department'].search([('din_id', '=', res.get('parentid'))])
                    if partner_department:
                        data.update({'parent_id': partner_department[0].id})
                h_department = self.env['hr.department'].search([('din_id', '=', res.get('id'))])
                if h_department:
                    h_department.sudo().write(data)
                else:
                    self.env['hr.department'].create(data)
        else:
            logging.info(">>>获取部门失败，原因为:{}".format(result.get('errmsg')))
            raise UserError("获取部门失败，原因为:{}".format(result.get('errmsg')))

