# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkReportListTran(models.TransientModel):
    _name = 'dingtalk.report.list.tran'
    _description = "获取用户日志"

    report_id = fields.Many2one(comodel_name='dingtalk.report.template', string=u'日志类型', required=True)
    start_time = fields.Datetime(string=u'开始时间', required=True)
    end_time = fields.Datetime(string=u'结束时间', required=True, default=fields.datetime.now())
    emp_ids = fields.Many2many(comodel_name='hr.employee', string=u'员工', required=True, domain="[('ding_id', '!=', False)]")

    def get_user_report_list(self):
        """
        获取用户日志
        :return:
        """
        self.ensure_one()
        user_list = list()
        for emp in self.emp_ids:
            user_list.append(emp.ding_id)
        client = dingtalk_api.get_client()
        cursor = 0
        size = 20
        while True:
            try:
                result = client.post('topapi/report/list', {
                    'start_time': dingtalk_api.datetime_to_stamp(self.start_time),
                    'end_time': dingtalk_api.datetime_to_stamp(self.end_time),
                    'template_name': self.report_id.name,
                    'userid': user_list,
                    'cursor': cursor,
                    'size': size
                })
            except Exception as e:
                raise UserError(e)
            if result.get('errcode') == 0:
                result = result.get('result')
                print(result)

                # 是否还有下一页
                if result.get('has_more'):
                    cursor += result.get('next_cursor')
                else:
                    break
            else:
                raise UserError('获取用户日志失败，详情为:{}'.format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}




