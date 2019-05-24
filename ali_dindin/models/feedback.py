# -*- coding: utf-8 -*-
import logging
import uuid
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingUserFeedback(models.Model):
    _description = '用户反馈'
    _name = 'dingding.user.feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    code = fields.Char(string='编号')
    name = fields.Char(string='反馈主题')
    body = fields.Text(string=u'反馈内容')
    response = fields.Text(string=u'回复结果')
    partner = fields.Char(string='联系人')
    contact_information = fields.Char(string='联系方式')
    remarks = fields.Text(string=u'备注')
    state = fields.Selection(string=u'反馈状态', selection=[('00', '草稿'), ('01', '等待答复'), ('02', '已回复')], default='00')

    @api.multi
    def commit_feedback(self):
        for res in self:
            raise UserError("暂未开通！")

    @api.model
    def create(self, values):
        values['code'] = str(uuid.uuid4())
        return super(DingDingUserFeedback, self).create(values)