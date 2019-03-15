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
    user_ids = fields.Many2many(comodel_name='hr.employee', relation='din_msg_and_emp_rel',
                                column1='din_msg_id', column2='emp_id', string=u'接受消息用户列表')
    dep_ids = fields.Many2many(comodel_name='hr.department', relation='din_msg_and_dep_rel',
                               column1='din_msg_id', column2='dep_id', string=u'接受部门消息列表')
    msg_type = fields.Selection(string=u'消息类型', selection=MESSAGETYPE, default='text', required=True)
    task_id = fields.Char(string='任务Id')
    state = fields.Selection(string=u'发送状态', selection=[('0', '未开始'), ('1', '处理中'), ('2', '处理完毕')],
                             default='0')
    text_message = fields.Text(string='文本消息内容')

    @api.multi
    def send_message(self):
        """发送消息函数"""
        logging.info(">>>开始钉钉发送工作消息")
        if self.user_ids or self.dep_ids:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'send_work_message')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'agent_id': self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_agentid'),  # 应用id
                # 'userid_list': department[0].din_id, # 用户userid
                # 'dept_id_list': 0,   # 部门id
                'to_all_user': 'true',   # 是否发送给企业全部用户 true/false
                'msg': {
                    'msgtype': self.msg_type,   # 消息类型
                    'text': {
                        "content": self.text_message,  # 消息内容
                    }
                }
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=30)
                result = json.loads(result.text)
                logging.info(">>>发送工作消息返回结果{}".format(result))
                if result.get('errcode') == 0:
                    self.write({'task_id': result.get('task_id'), 'state': '1'})
                    self.message_post(body=u"消息信息已推送到钉钉，钉钉正在加急处理中!", message_type='notification')
                else:
                    raise UserError('发送消息失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")

        else:
            raise UserError("请选择发送的员工或部门!")
