# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

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
    title = fields.Char(string='标题')

    @api.multi
    def summit_approval(self):
        """
        提交审批按钮，将单据审批信息发送到钉钉
        :return:
        """
        pass

    @api.multi
    def unlink(self):
        for res in self:
            if res.oa_state != '00':
                raise UserError('非草稿单据不能删除!')
        super(DinDinApprovalMain, self).unlink()

    @api.model
    def _summit_din_approval(self, process_code, user_id, dept_id, approvers, cc_list, form_values):
        """
        提交到钉钉进行审批
        :param process_code:审批模型编码
        :param user_id:发起人userid
        :param dept_id:发起人部门id
        :param approvers:抄送人
        :param cc_list:抄送人
        :param form_values:表单参数
        :return: 审批实例id
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'processinstance_create')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'process_code': process_code,  # 审批模型编码
            'originator_user_id': user_id,  # 发起人userid
            'dept_id': dept_id,  # 发起人部门id
            'approvers': approvers,  # 审批人
            'cc_list': cc_list,  # 抄送人
            'form_component_values': form_values  # 表单参数
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            logging.info(">>>提交审批到钉钉返回结果{}".format(result))
            if result.get('errcode') == 0:
                return result.get('process_instance_id')
            else:
                raise UserError('提交审批失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")

    @api.model
    def _check_oa_model(self, model_name):
        """
        检查oa模型与审批单据的关联
        :param model_name:
        :return:
        """
        model_id = self.env['ir.model'].sudo().search([('model', '=', model_name)]).id
        dac = self.env['dindin.approval.control'].search([('oa_model_id', '=', model_id)])
        if not dac:
            raise UserError("没有对应的审批关联！请前往钉钉->审批关联中进行配置!")
        return dac[0].template_id.process_code

    @api.model
    def _get_user_and_cc_list(self, users_ids, cc_ids):
        """
        根据单据上的审批人列表和抄送人列表拼接为字符串并返回
        :param users_ids: 审批人列表
        :param cc_ids: 抄送人列表
        :return:
        """
        # 审批人
        user_str = ''
        for user in users_ids:
            if user_str == '':
                user_str = user_str + "{}".format(user.emp_id.din_id)
            else:
                user_str = user_str + ",{}".format(user.emp_id.din_id)
        # 抄送人
        cc_str = ''
        for user in cc_ids:
            if cc_str == '':
                cc_str = cc_str + "{}".format(user.emp_id.din_id)
            else:
                cc_str = cc_str + ",{}".format(user.emp_id.din_id)
        return user_str, cc_str

    @api.multi
    def _get_user_and_dept(self):
        """
        返回发起人钉钉id和部门id
        :return:
        """
        for res in self:
            return res.originator_user_id.din_id, res.originator_user_id.department_id.din_id

    def _check_lines(self, approval_users_ids, cc_ids):
        """
        检查审批人列表和抄送人是否为空
        :param approval_users_ids:
        :param cc_ids:
        :return:
        """
        if len(approval_users_ids) == 0:
            raise UserError("审批人列表不能为空!")
        if len(cc_ids) == 0:
            raise UserError("抄送人列表不能为空!")
        return True


class DinDinApproversUsers(models.Model):
    _name = 'dindin.approval.users'
    _description = u"审批人列表"
    _rec_name = 'emp_id'

    number = fields.Integer(string=u'序号')
    sequence = fields.Integer(string=u'序号')
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

    @api.onchange('sequence')
    def onchange_sequence(self):
        self.number = self.sequence + 1


class DinDinApproversCc(models.Model):
    _name = 'dindin.approval.cc'
    _description = u"抄送人列表"
    _rec_name = 'emp_id'

    number = fields.Integer(string=u'序号')
    sequence = fields.Integer(string=u'序号')
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

    @api.onchange('sequence')
    def onchange_sequence(self):
        self.number = self.sequence + 1
