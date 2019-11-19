# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DingTalkReport(models.Model):
    _name = 'dingtalk.report.report'
    _description = '日志列表'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id'

    VISITTYPE = [
        ('1', '当面拜访'), ('2', '电话拜访'), ('3', '聊天软件'), ('4', '其他方式')
    ]

    name = fields.Char(string='主题')
    category_id = fields.Many2one('dingtalk.report.category', string="日志类型", required=True)
    date = fields.Datetime(string="日期", default=fields.date.today())
    attachment_number = fields.Integer('附件数', compute='_compute_attachment_number')
    today_work = fields.Text(string=u'今日完成工作')
    no_compute_work = fields.Text(string=u'未完成工作')
    coordination_work = fields.Text(string=u'需协调工作')
    week_compute = fields.Text(string=u'本周完成工作')
    week_summary = fields.Text(string=u'本周工作总结')
    next_week_plan = fields.Text(string=u'下周工作计划')
    month_work = fields.Text(string=u'本月工作内容')
    month_summary = fields.Text(string=u'本月工作总结')
    next_month_plan = fields.Text(string=u'下月工作计划')
    visit_partner = fields.Many2one(comodel_name='res.partner', string=u'拜访对象')
    visit_type = fields.Selection(string=u'拜访方式', selection=VISITTYPE, default='1')
    visit_matter = fields.Text(string=u'主要事宜')
    visit_result = fields.Text(string=u'拜访结果')
    today_urnover_performance = fields.Float(string=u'今日营业额')
    today_partner_performance = fields.Integer(string=u'今日客户数')
    monthly_ct_performance = fields.Float(string=u'月累计营业额')
    month_pt_performance = fields.Float(string=u'本月业绩目标')
    thinking_today_performance = fields.Text(string=u'今日思考')
    # ---------
    has_today_work = fields.Selection(related="category_id.has_today_work")
    has_no_compute_work = fields.Selection(related="category_id.has_no_compute_work")
    has_coordination_work = fields.Selection(related="category_id.has_coordination_work")
    has_week_compute = fields.Selection(related="category_id.has_week_compute")
    has_week_summary = fields.Selection(related="category_id.has_week_summary")
    has_next_week_plan = fields.Selection(related="category_id.has_next_week_plan")
    has_month_work = fields.Selection(related="category_id.has_month_work")
    has_month_summary = fields.Selection(related="category_id.has_month_summary")
    has_next_month_plan = fields.Selection(related="category_id.has_next_month_plan")
    has_visit_partner = fields.Selection(related="category_id.has_visit_partner")
    has_visit_type = fields.Selection(related="category_id.has_visit_type")
    has_visit_matter = fields.Selection(related="category_id.has_visit_matter")
    has_visit_result = fields.Selection(related="category_id.has_visit_result")
    has_today_urnover_performance = fields.Selection(related="category_id.has_today_urnover_performance")
    has_today_partner_performance = fields.Selection(related="category_id.has_today_partner_performance")
    has_monthly_ct_performance = fields.Selection(related="category_id.has_monthly_ct_performance")
    has_month_pt_performance = fields.Selection(related="category_id.has_month_pt_performance")
    has_thinking_today_performance = fields.Selection(related="category_id.has_thinking_today_performance")
    has_date = fields.Selection(related="category_id.has_date")

    report_id = fields.Char(string='唯一ID')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    report_time = fields.Datetime(string=u'日志时间', default=fields.datetime.now())

    def _compute_attachment_number(self):
        domain = [('res_model', '=', 'dingtalk.report.report'), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for request in self:
            request.attachment_number = attachment.get(request.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'dingtalk.report.report'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'dingtalk.report.report', 'default_res_id': self.id}
        return res


