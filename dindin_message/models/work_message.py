# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MESSAGETYPE = [
    ('text', '文本消息'),
    ('image', '图片消息'),
    ('voice', '语音消息'),
    ('file', '文件消息'),
    ('link', '链接消息'),
    ('oa', 'OA消息'),
    ('markdown', 'Markdown'),
    ('action_card', '卡片消息'),
]


class DinDinWorkMessage(models.Model):
    _name = 'dindin.work.message'
    _description = "钉钉工作消息"
    _inherit = ['mail.thread']
    _rec_name = 'name'

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    name = fields.Char(string='标题', required=True)
    to_all_user = fields.Boolean(string=u'发送给企业全部用户')
    user_ids = fields.One2many(comodel_name='dindin.work.message.user.list', inverse_name='message_id',
                               string=u'接受消息用户列表')
    dep_ids = fields.One2many(comodel_name='dindin.work.message.dept.list', inverse_name='message_id',
                              string=u'接受部门消息列表')
    msg_type = fields.Selection(string=u'消息类型', selection=MESSAGETYPE, default='text', required=True)
    task_id = fields.Char(string='任务Id')
    state = fields.Selection(string=u'发送状态', selection=[('0', '未开始'), ('1', '处理中'), ('2', '处理完毕')],
                             default='0')
    text_message = fields.Text(string='文本消息内容', required=True)

    @api.onchange('user_ids', 'dep_ids')
    @api.constrains('user_ids', 'dep_ids')
    def check_length(self):
        if len(self.user_ids) > 6:
            if not self.to_all_user:
                raise UserError('用户列表最大支持20个，请不要超过20个用户')
        if len(self.dep_ids) > 6:
            if not self.to_all_user:
                raise UserError('接受消息部门列表最大支持20')

    @api.onchange('to_all_user')
    def onchange_to_all_users(self):
        if self.to_all_user:
            self.user_ids = False
            emps = self.env['hr.employee'].sudo().search([('din_id', '!=', '')])
            user_list = list()
            for emp in emps:
                user_list.append({
                    'emp_id': emp.id,
                    'mobile_phone': emp.mobile_phone,
                    'job_title': emp.job_title,
                    'department_id': emp.department_id.id,
                    'msg_type': '03',
                })
            self.user_ids = user_list

    @api.multi
    def send_message(self):
        """发送消息函数"""
        user_str = ''
        dept_str = ''
        for user in self.user_ids:
            if user_str == '':
                user_str = user_str + "{}".format(user.emp_id.din_id)
            else:
                user_str = user_str + ",{}".format(user.emp_id.din_id)
        for dept in self.dep_ids:
            if dept_str == '':
                dept_str = dept_str + "{}".format(dept.dept_id.din_id)
            else:
                dept_str = dept_str + ",{}".format(dept.dept_id.din_id)
        msg = {
            'msgtype': self.msg_type,  # 消息类型
            'text': {
                "content": self.text_message,  # 消息内容
            }
        }
        task_id = self.send_work_message(toall=self.to_all_user, userstr=user_str, deptstr=dept_str, msg=msg)
        self.write({'task_id': task_id, 'state': '1'})
        self.message_post(body=u"消息信息已推送到钉钉，钉钉正在加急处理中!", message_type='notification')

    @api.model
    def send_work_message(self, toall=None, userstr=None, deptstr=None, msg=None):
        """
        发送工作消息功能函数，其他模型可调用本方法传递需要接受的用户和消息，当toall参数为true时，userids用户列表和deptids部门列表可不传递。
        即 toall、userids、deptids三个参数必须传递一个。
        :param toall: boolean值，是否发送企业全部人员
        :param userstr: string，接受用户列表，注意：需要传递员工模型中的din_id字段
        :param deptstr: ；string，接受部门列表，需传递部门的din_id字段
        :param msg:   消息体，请参照钉钉提供的消息体格式
        :return task_id: 返回钉钉消息任务id。
        """
        logging.info(">>>开始钉钉发送工作消息")
        if not toall and not userstr and not deptstr:
            raise UserError("是否发送全部员工、用户列表、部门列表三个参数必须有一个有值！")
        if msg:
            if not isinstance(msg, dict):
                raise UserError("需要发送的消息体msg参数格式不正确！")
        else:
            raise UserError("需要发送的消息体不存在！")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'send_work_message')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'agent_id': self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_agentid'),  # 应用id
            'msg': msg if msg else {}
        }
        if toall:
            data.update({'to_all_user': 'true'})
        else:
            if userstr:
                data.update({'userid_list': userstr})
            else:
                data.update({'dept_id_list': deptstr})
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(">>>发送工作消息返回结果{}".format(result))
            if result.get('errcode') == 0:
                return result.get('task_id')
            else:
                raise UserError('发送消息失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")

    @api.multi
    def search_message_state(self):
        """
        查询消息进度
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'search_work_message')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'agent_id': self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_agentid'),  # 应用id
            'task_id': self.task_id
        }
        headers = {'Content-Type': 'application/json'}
        logging.info(data)
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                   timeout=30)
            result = json.loads(result.text)
            logging.info(">>>查询工作消息状态返回结果{}".format(result))
            if result.get('errcode') == 0:
                progress = result.get('progress')
                self.write({'state': str(progress.get('status'))})
                self.message_post(body=u"查询消息进度成功，返回值:{}!".format(result), message_type='notification')
            else:
                raise UserError('查询工作消息状态，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")

    @api.multi
    def search_message_result(self):
        """查询工作通知消息的发送结果"""
        logging.info(">>>开始查询工作通知消息的发送结果")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'work_message_result')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'agent_id': self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_agentid'),  # 应用id
            'task_id': self.task_id
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                   timeout=30)
            result = json.loads(result.text)
            logging.info(">>>查询工作消息状态返回结果{}".format(result))
            if result.get('errcode') == 0:
                send_result = result.get('send_result')
                failed_user_id_list = send_result.get('failed_user_id_list')  # 失败的用户列表
                read_user_id_list = send_result.get('read_user_id_list')      # 已读消息的用户id
                unread_user_id_list = send_result.get('unread_user_id_list')  # 未读消息的用户id
                invalid_dept_id_list = send_result.get('invalid_dept_id_list')  # 无效的部门id
                for failed in failed_user_id_list:
                    for user in self.user_ids:
                        if user.emp_id.din_id == failed:
                            user.write({'msg_type': '00'})
                for read in read_user_id_list:
                    for user in self.user_ids:
                        if user.emp_id.din_id == read:
                            user.write({'msg_type': '02'})
                for unread in unread_user_id_list:
                    for user in self.user_ids:
                        if user.emp_id.din_id == unread:
                            user.write({'msg_type': '01'})
                for invalid in invalid_dept_id_list:
                    for dept in self.dep_ids:
                        if dept.dept_id.din_id == invalid:
                            dept.write({'msg_type': '00'})
                self.message_post(body=u"查询工作通知消息的发送结果成功", message_type='notification')
            else:
                raise UserError('查询工作通知消息的发送结果失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")


class DinDinWorkMessageUserList(models.Model):
    _name = 'dindin.work.message.user.list'
    _rec_name = 'emp_id'
    _description = "工作消息用户列表"

    MESSGAETYPE = [
        ('00', '失败'),
        ('01', '未读'),
        ('02', '已读'),
        ('03', '未发送')
    ]

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    mobile_phone = fields.Char(string='电话')
    job_title = fields.Char(string='职位')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', ondelete='cascade')
    msg_type = fields.Selection(string=u'消息状态', selection=MESSGAETYPE, default='03')
    message_id = fields.Many2one(comodel_name='dindin.work.message', string=u'消息', ondelete='cascade')

    @api.onchange('emp_id')
    def onchange_emp(self):
        if self.emp_id:
            self.mobile_phone = self.emp_id.mobile_phone
            self.job_title = self.emp_id.job_title
            self.department_id = self.emp_id.department_id.id


class DinDinWorkMessageDeptList(models.Model):
    _name = 'dindin.work.message.dept.list'
    _rec_name = 'dept_id'
    _description = "工作消息部门列表"

    MESSGAETYPE = [
        ('00', '失败'),
        ('01', '未读'),
        ('02', '已读'),
        ('03', '未发')
    ]

    dept_id = fields.Many2one(comodel_name='hr.department', string=u'部门', ondelete='cascade', required=True)
    msg_type = fields.Selection(string=u'消息状态', selection=MESSGAETYPE, default='03')
    message_id = fields.Many2one(comodel_name='dindin.work.message', string=u'消息', ondelete='cascade')
