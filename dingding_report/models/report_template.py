# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingReportTemplate(models.Model):
    _name = 'dingding.report.template'
    _description = "日志模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    report_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_all_template(self):
        """获取日志模板"""
        group = self.env.user.has_group('dingding_report.dd_get_report_templategroup')
        if not group:
            raise UserError("不好意思，你没有权限进行本操作！")
        url = self.env['dingding.parameter'].search([('key', '=', 'report_template_listbyuserid')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        data = {
            'offset': 0,
            'size': 100,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                d_res = result.get('result')
                for report in d_res.get('template_list'):
                    data = {
                        'name': report.get('name'),
                        'icon_url': report.get('icon_url'),
                        'report_code': report.get('report_code'),
                        'url': report.get('url'),
                    }
                    template = self.env['dingding.report.template'].search(
                        [('report_code', '=', report.get('report_code'))])
                    if template:
                        template.write(data)
                    else:
                        self.env['dingding.report.template'].create(data)
            else:
                raise UserError('获取日志模板失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")

    @api.model
    def get_user_unread_count(self):
        """
        根据当前用户获取该用户的未读日志数量
        :return:
        """
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
        if len(emp) > 1:
            return {'state': False, 'number': 0, 'msg': '登录用户关联了多个员工'}
        if emp and emp.ding_id:
            url = self.env['dingding.parameter'].search([('key', '=', 'report_getunreadcount')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            data = {
                'userid': emp.ding_id,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    return {'state': True, 'number': result.get('count')}
                else:
                    return {'state': False, 'number': 0, 'msg': result.get('errmsg')}
            except ReadTimeout:
                return {'state': False, 'number': 0, 'msg': '网络连接超时'}
            except Exception as e:
                return {'state': False, 'number': 0, 'msg': "网络连接失败"}
        else:
            return {'state': False, 'number': 0, 'msg': 'None'}