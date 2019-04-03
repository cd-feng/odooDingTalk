# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DinDinApprovalMain(models.Model):
    _name = 'dindin.approval.main'
    _inherit = ['mail.thread']
    _description = "审批表单基类"

    OASTATE = [
        ('00', '草稿'),
        ('01', '审批中'),
        ('02', '审批结束'),
    ]
    OARESULT = [
        ('agree', '同意'),
        ('refuse', '拒绝'),
        ('redirect', '转交'),
    ]

    process_code = fields.Char(string='单据编号')
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    originator_user_id = fields.Many2one(comodel_name='hr.employee', string=u'发起人', required=True)
    oa_state = fields.Selection(string=u'单据状态', selection=OASTATE, default='00')
    oa_message = fields.Char(string='审批消息')
    process_instance_id = fields.Char(string='钉钉审批实例id')
    reason_leave = fields.Text(string=u'事由')
    oa_result = fields.Selection(string=u'审批结果', selection=OARESULT)
    oa_url = fields.Char(string='钉钉单据url')

    @api.multi
    def summit_approval(self):
        """
        提交审批按钮，将单据审批信息发送到钉钉
        :return:
        """
        pass


class DinDinApproversUsers(models.Model):
    _name = 'dindin.approval.users'
    _description = u"审批人列表"
    _rec_name = 'emp_id'
    
    number = fields.Integer(string=u'序号')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'审批人', required=True)
    mobile_phone = fields.Char(string='电话')
    job_title = fields.Char(string='职位')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', ondelete='cascade')

    @api.onchange('emp_id')
    def onchange_emp(self):
        if self.emp_id:
            self.mobile_phone = self.emp_id.mobile_phone
            self.job_title = self.emp_id.job_title
            self.department_id = self.emp_id.department_id.id


class DinDinApproversCc(models.Model):
    _name = 'dindin.approval.cc'
    _description = u"抄送人列表"
    _rec_name = 'emp_id'

    number = fields.Integer(string=u'序号')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'抄送人', required=True)
    mobile_phone = fields.Char(string='电话')
    job_title = fields.Char(string='职位')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', ondelete='cascade')

    @api.onchange('emp_id')
    def onchange_emp(self):
        if self.emp_id:
            self.mobile_phone = self.emp_id.mobile_phone
            self.job_title = self.emp_id.job_title
            self.department_id = self.emp_id.department_id.id
