# -*- coding: utf-8 -*-

import base64
from odoo import fields, models, _
from odoo.modules.module import get_module_resource


CATEGORY_SELECTION = [
    ('required', '必填'),
    ('optional', '可选'),
    ('no', '无')]


class ReportCategory(models.Model):
    _name = 'dingtalk.report.category'
    _description = '日志类型'
    _order = 'id'

    def _get_default_image(self):
        default_image_path = get_module_resource('mail', 'static/src/img', 'groupdefault.png')
        return base64.b64encode(open(default_image_path, 'rb').read())

    active = fields.Boolean(default=True)
    name = fields.Char(string='日志名称', required=True)
    image = fields.Binary(string='Image', default=_get_default_image)
    description = fields.Char(string="描述", required=True)

    has_today_work = fields.Selection(string=u'今日完成工作', selection=CATEGORY_SELECTION, required=True, default='no')
    has_no_compute_work = fields.Selection(string=u'未完成工作', selection=CATEGORY_SELECTION, required=True, default='no')
    has_coordination_work = fields.Selection(string=u'需协调工作', selection=CATEGORY_SELECTION, required=True, default='no')

    has_week_compute = fields.Selection(string=u'本周完成工作', selection=CATEGORY_SELECTION, required=True, default='no')
    has_week_summary = fields.Selection(string=u'本周工作总结', selection=CATEGORY_SELECTION, required=True, default='no')
    has_next_week_plan = fields.Selection(string=u'下周工作计划', selection=CATEGORY_SELECTION, required=True, default='no')

    has_month_work = fields.Selection(string=u'本月工作内容', selection=CATEGORY_SELECTION, required=True, default='no')
    has_month_summary = fields.Selection(string=u'本月工作总结', selection=CATEGORY_SELECTION, required=True, default='no')
    has_next_month_plan = fields.Selection(string=u'下月工作计划', selection=CATEGORY_SELECTION, required=True, default='no')

    has_visit_partner = fields.Selection(string=u'拜访对象', selection=CATEGORY_SELECTION, required=True, default='no')
    has_visit_type = fields.Selection(string=u'拜访方式', selection=CATEGORY_SELECTION, required=True, default='no')
    has_visit_matter = fields.Selection(string=u'主要事宜', selection=CATEGORY_SELECTION, required=True, default='no')
    has_visit_result = fields.Selection(string=u'拜访结果', selection=CATEGORY_SELECTION, required=True, default='no')

    has_today_urnover_performance = fields.Selection(string=u'今日营业额', selection=CATEGORY_SELECTION, required=True, default='no')
    has_today_partner_performance = fields.Selection(string=u'今日客户数', selection=CATEGORY_SELECTION, required=True, default='no')
    has_monthly_ct_performance = fields.Selection(string=u'月累计营业额', selection=CATEGORY_SELECTION, required=True, default='no')
    has_month_pt_performance = fields.Selection(string=u'本月业绩目标', selection=CATEGORY_SELECTION, required=True, default='no')
    has_thinking_today_performance = fields.Selection(string=u'今日思考', selection=CATEGORY_SELECTION, required=True, default='no')

    has_date = fields.Selection(string=u'日期', selection=CATEGORY_SELECTION, required=True, default='required')

    def create_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "dingtalk.report.report",
            "views": [[False, "form"]],
            "context": {
                'form_view_initial_mode': 'edit',
                'default_name': "{}：{}".format(fields.date.today(), self.name),
                'default_category_id': self.id,
            },
        }

    def get_dingtalk_report_list(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "dingtalk.report.list.tran",
            "target": 'new',
            "views": [[False, "form"]],
            "context": {
                'form_view_initial_mode': 'edit',
            },
        }
