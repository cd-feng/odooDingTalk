# -*- coding: utf-8 -*-
import datetime
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dd_step_count = fields.Integer(string=u'运动步数', compute='get_dept_today_health')

    @api.multi
    def get_dept_today_health(self):
        """
        获取部门在今日的步数
        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_dept_health_info'):
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'get_health_list')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            for res in self:
                if res.din_id:
                    today = datetime.date.today()
                    formatted_today = today.strftime('%Y%m%d')
                    data = {
                        'type': 1,
                        'object_id': res.din_id,
                        'stat_dates': formatted_today,
                    }
                    headers = {'Content-Type': 'application/json'}
                    try:
                        result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                               timeout=1)
                        result = json.loads(result.text)
                        logging.info(result)
                        if result.get('errcode') == 0:
                            for stepinfo_list in result.get('stepinfo_list'):
                                res.update({'dd_step_count': stepinfo_list['step_count']})
                        else:
                            res.update({'dd_step_count': 0})
                    except ReadTimeout:
                        logging.info(">>>获取运动数据超时！")
                else:
                    res.update({'dd_step_count': 0})
