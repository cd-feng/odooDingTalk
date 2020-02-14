# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models, _
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
        if not self.report_id.category_id:
            raise UserError(_("请先在钉钉日志模板中关联系统日志类别!"))
        user_list = list()
        for emp in self.emp_ids:
            user_list.append(emp.ding_id)
        cursor = 0
        size = 20
        report_dict = self._get_report_dicts()
        while True:
            try:
                result = dingtalk_api.get_client().post('topapi/report/list', {
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
                data_list = result.get('data_list')
                for data in data_list:
                    # 封装字段数据
                    report_data = dict()
                    for contents in data.get('contents'):
                        report_data.update({report_dict.get(contents.get('key')): contents.get('value')})
                    # 读取创建人
                    employee = self.env['hr.employee'].search([('ding_id', '=', data.get('creator_id'))], limit=1)
                    report_data.update({
                        'name': data.get('template_name'),
                        'category_id': self.report_id.category_id.id or False,
                        'employee_id': employee.id or False,
                        'report_time': dingtalk_api.timestamp_to_local_date(data.get('create_time')) or fields.datetime.now(),
                    })
                    reports = self.env['dingtalk.report.report'].search([('report_id', '=', data.get('report_id'))])
                    if not reports:
                        self.env['dingtalk.report.report'].create(report_data)
                # 是否还有下一页
                if result.get('has_more'):
                    cursor += result.get('next_cursor')
                else:
                    break
            else:
                raise UserError('获取用户日志失败，详情为:{}'.format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}

    def _get_report_dicts(self):
        """
        将日志字段转换为dict
        :return:
        """
        report_model = self.env['ir.model'].sudo().search([('model', '=', 'dingtalk.report.report')])
        data_dict = dict()
        for field in report_model.field_id:
            if field.name[:4] != 'has_':
                data_dict.update({field.field_description: field.name})
        return data_dict




