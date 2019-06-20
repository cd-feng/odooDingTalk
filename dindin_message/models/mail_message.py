# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        message = super(MailMessage, self).create(values)
        template = self.env['dingding.message.template'].sudo()
        model = self.env['ir.model'].sudo().search([('model', '=', values.get('model'))])
        results = template.get_template_by_model_and_type(model, values.get('message_type'))
        if results:
            for result in results:
                # 备注消息
                if values.get('message_type') == 'comment':
                    partner = self.env['res.partner'].sudo().search([('id', '=', values.get('author_id'))])
                    base_url = "{}/dingding/auto/login/in".format(self.env["ir.config_parameter"].get_param("web.base.url"))
                    msg = "**{}** 在 **{}({})** 上备注: \n  \n *{}*  \n  [登录ERP]({})".format(
                        partner.name, model.name, values.get('record_name'), values.get('body'), base_url)
                    # 发送到群
                    if result.send_to == 'chat':
                        for chat in result.chat_ids:
                            self.env['dingding.send.chat.message'].sudo().send_message(chat, msg)
                    # 发送到指定人
                    elif result.send_to == 'user':
                        user_str = ''
                        for user in result.user_ids:
                            if user.din_id:
                                if user_str == '':
                                    user_str = user_str + "{}".format(user.din_id)
                                else:
                                    user_str = user_str + ",{}".format(user.din_id)
                        self.env['dingding.send.chat.message'].sudo().send_work_message(user_str, msg)
                    # 指定单据发送人
                    elif result.send_to == 'form':
                        user_str = ''
                        for field in result.field_ids:
                            sql = "SELECT {} FROM {} WHERE id = {}".format(field.name, values['model'].replace('.', '_'), values['res_id'])
                            logging.info(sql)
                            self.env.cr.execute(sql)
                            model_result = self.env.cr.fetchone()
                            if model_result:
                                emp = self.env['hr.employee'].sudo().search([('user_id', '=', model_result[0])])
                                if emp.din_id:
                                    if user_str == '':
                                        user_str = user_str + "{}".format(emp.din_id)
                                    else:
                                        user_str = user_str + ",{}".format(emp.din_id)
                        self.env['dingding.send.chat.message'].sudo().send_work_message(user_str, msg)
                    # 指定群机器人
                    elif result.send_to == 'robot':
                        self.env['dingding.robot'].sudo().send_robot_message(result.rotbot_ids, msg)
        return message


class DingDingMessageTemplate(models.Model):
    _name = 'dingding.message.template'
    _description = "钉钉消息模板"
    _rec_name = 'name'

    SENDTOTYPE = [
        ('chat', '钉钉群'),
        ('user', '指定人'),
        ('form', '单据人员'),
        ('robot', '群机器人'),
    ]

    name = fields.Char(string='消息名称', required=True)
    model_id = fields.Many2one(comodel_name='ir.model', string=u'应用模型', required=True)
    subject = fields.Char(string='消息主题')
    body = fields.Text(string=u'内容')
    active = fields.Boolean(default=True)
    email = fields.Boolean(string=u'Email消息时触发')
    comment = fields.Boolean(string=u'备注消息时触发')
    notification = fields.Boolean(string=u'讨论消息时触发')
    chat_id = fields.Many2one(comodel_name='dingding.chat', string=u'To群会话')
    send_to = fields.Selection(string=u'发送到', selection=SENDTOTYPE, default='chat', required=True)
    chat_ids = fields.Many2many(comodel_name='dingding.chat', relation='message_template_and_dingding_chat_rel',
                                column1='template_id', column2='chat_id', string=u'群会话')
    user_ids = fields.Many2many('hr.employee', string='接受人')
    field_ids = fields.Many2many('ir.model.fields', string=u'单据字段')
    rotbot_ids = fields.Many2many('dingding.robot', string=u'群机器人')

    @api.model
    def generate_message_text(self, model_name, body_html, res_id):
        """
        根据Mako语法生成消息文本
        :param model_name: 模型
        :param body_html:内容
        :param res_id: 单据id
        :return:
        """
        result = self.env['mail.template'].sudo()._render_template(body_html, model_name, res_id)
        return result

    @api.model
    def get_template_by_model_and_type(self, model, msh_type):
        if model and msh_type:
            template = self.env['dingding.message.template'].sudo().search(
                [('model_id', '=', model.id), (msh_type, '=', True), ('active', '=', True)])
            return template if template else False
        return False

    @api.onchange('model_id', 'send_to')
    def _change_model_id(self):
        if not self.model_id:
            return {'domain': {'field_ids': expression.FALSE_DOMAIN}}
        model_fields_domain = [
            ('store', '=', True), ('ttype', '=', 'many2one'), ('relation', '=', 'res.users'),
            '|', ('model_id', '=', self.model_id.id),
                 ('model_id', 'in', self.model_id.inherited_model_ids.ids)]
        return {'domain': {'field_ids': model_fields_domain}}
