# -*- coding: utf-8 -*-
import inspect
import logging
import sys
from lxml import etree
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingtalkMsgConfig(models.Model):
    _description = "消息模板"
    _name = 'dingtalk.message.config'
    _order = 'id desc'

    def _compute_domain(self):
        all_cls = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        odoo_cls = [getattr(cls[1], '_name') for cls in all_cls if cls[1].__bases__[0].__name__ == 'Model']   # 排除当前的对象
        odoo_cls += [model.model for model in self.env['ir.model'].search([('transient', '=', True)])]        # 排除临时对象
        return [('model', 'not in', odoo_cls)]

    name = fields.Char(string="模板名称", required=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)
    state = fields.Selection(string="状态", selection=[('open', '开放'), ('close', '关闭')], default='close')
    MessageOpportunity = [
        ('normal', '常规操作触发'),
        ('button', '指定按钮触发'),
        ('new_user', '新用户通知(仅系统用户模型有效)'),
    ]
    msg_opportunity = fields.Selection(string="推送时机", selection=MessageOpportunity, default='normal')

    message_timing = fields.Selection(string="触发时机", selection=[('save', '保存'), ('write', '更新'), ('unlink', '删除')],
                                      default='save')
    MsgType = [
        ('notice', '工作通知'),
        ('chat', '企业群'),
        ('robot', '群机器人'),
    ]
    ttype = fields.Selection(string="推送到", selection=MsgType, default='notice')
    to_all_user = fields.Boolean(string="发送给全部用户?")
    user_ids = fields.Many2many('hr.employee', 'dingtalk_messgage_employee_rel',
                                string="接受消息用户", domain="[('ding_id', '!=', '')]")
    department_ids = fields.Many2many('hr.department', 'dingtalk_messgage_department_rel',
                                      string="接受消息部门", domain="[('ding_id', '!=', '')]")
    chat_id = fields.Many2one(comodel_name="dingtalk.mc.chat", string="群会话")
    robot_id = fields.Many2one(comodel_name="dingtalk.chat.robot", string="群机器人")
    model_id = fields.Many2one('ir.model', string=u'应用于', index=True, ondelete="set null", domain=_compute_domain)

    button_ids = fields.Many2many('dingtalk.message.config.but', 'dingtalk_message_config_button_rel',
                                  string=u'指定按钮',
                                  domain="[('model_id', '=', model_id), ('company_id', '=', company_id)]")
    msg_title = fields.Char(string="消息标题")
    msg_body = fields.Text(string="消息内容")

    def open_state(self):
        """
        打开消息通知
        :return:
        """
        self.ensure_one()
        # 检查
        if self.msg_opportunity == 'new_user':
            result = self.search_count([('msg_opportunity', '=', 'new_user'), ('state', '=', 'open')])
            if result > 1:
                raise ValidationError("您已配置了新用户通知的模板，不允许开启多个！")
        self.write({'state': 'open'})

    def close_state(self):
        """
        :return:
        """
        self.ensure_one()
        self.write({'state': 'close'})

    @api.onchange('model_id')
    def onchange_model_id(self):
        """
        根据选择的模型读取模型动作按钮
        :return:
        """
        for rec in self:
            if rec.model_id:
                model_id = rec.model_id
                result = self.env[model_id.model].fields_view_get()
                root = etree.fromstring(result['arch'])
                config_but = self.env['dingtalk.message.config.but']
                for item in root.xpath("//header/button"):
                    domain = [('model_id', '=', model_id.id), ('function', '=', item.get('name')), ('company_id', '=', rec.company_id.id)]
                    model_buts = config_but.search(domain)
                    if not model_buts:
                        config_but.create({
                            'model_id': model_id.id,
                            'name': item.get('string'),
                            'function': item.get('name'),
                            'modifiers': item.get('modifiers'),
                            'company_id': rec.company_id.id,
                        })

    @api.model
    def is_new_user_send_msg(self):
        """
        是否发送信件用户消息
        :return:
        """
        domain = [('msg_opportunity', '=', 'new_user'), ('company_id', '=', self.env.user.company_id.id)]
        result = self.search(domain, limit=1)
        if len(result) > 0:
            return result
        return False


class DingtalkMsgConfigButton(models.Model):
    _description = "消息模板按钮"
    _name = 'dingtalk.message.config.but'
    _order = 'id desc'

    model_id = fields.Many2one('ir.model', string='模型', index=True)
    model_model = fields.Char(string='模型名', related='model_id.model', store=True, index=True)
    name = fields.Char(string="按钮名称", index=True)
    function = fields.Char(string='按钮方法', index=True)
    modifiers = fields.Char(string="按钮属性值")
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)

    def name_get(self):
        return [(rec.id, "%s: %s" % (rec.model_id.name, rec.name)) for rec in self]