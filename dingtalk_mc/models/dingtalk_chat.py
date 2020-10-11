# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingTalkMcChat(models.Model):
    _name = 'dingtalk.mc.chat'
    _description = "钉钉群会话"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    def _get_default_image(self):
        default_image_path = get_module_resource('dingtalk_mc', 'static/src/img', 'default_image.png')
        return base64.b64encode(open(default_image_path, 'rb').read())

    chat_id = fields.Char(string='群会话Id')
    chat_icon = fields.Char(string='群头像mediaId')
    name = fields.Char(string='群名称', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='公司', default=lambda self: self.env.user.company_id.id)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='群主', required=True)
    show_history_type = fields.Selection(string='聊天历史消息', selection=[('0', '否'), ('1', '是'), ], default='0')
    searchable = fields.Selection(string='群可搜索', selection=[('0', '否'), ('1', '是'), ], default='0')
    validation_type = fields.Selection(string='入群验证', selection=[('0', '否'), ('1', '是'), ], default='0')
    mention_all_authority = fields.Selection(string='@all 权限', selection=[('0', '所有人'), ('1', '仅群主'), ], default='0')
    chat_banned_type = fields.Selection(string='群禁言', selection=[('0', '不禁言'), ('1', '全员禁言'), ], default='0')
    management_ype = fields.Selection(string='管理类型', selection=[('0', '所有人可管理'), ('1', '仅群主可管理')], default='1')
    useridlist = fields.Many2many(comodel_name='hr.employee', relation='dingtalk_chat_and_hr_employee_rel',
                                  column1='chat_id', column2='emp_id', string='群成员', required=True)
    state = fields.Selection(string='状态', selection=[('new', '新建'), ('normal', '已建立'), ('close', '解散')],
                             default='new', track_visibility='onchange')
    channel_ids = fields.Many2many(comodel_name='mail.channel', relation='dingtalk_chat_and_mail_channel_rel',
                                   column1='chat_id', column2='mail_id', string='关注频道')
    model_ids = fields.Many2many(comodel_name='ir.model', relation='dingtalk_chat_and_ir_model_rel',
                                 column1='chat_id', column2='model_id', string='关联模型')
    image = fields.Binary("照片", default=_get_default_image)
    robot_count = fields.Integer(string='群机器人数', compute='_compute_get_robot_count')
    active = fields.Boolean(default=True)

    def _compute_get_robot_count(self):
        """
        获取当前群的群机器人数量
        :return:
        """
        for res in self:
            res.robot_count = self.env['dingtalk.chat.robot'].search_count([('chat_id', '=', res.id)])

    def action_view_robot(self):
        """
        跳转到群机器人列表
        :return:
        """
        self.ensure_one()
        action = self.env.ref('dingtalk_mc.dingtalk_chat_robot_action').read()[0]
        action['domain'] = [('chat_id', '=', self.id)]
        return action

    def create_dingtalk_chat(self):
        """
        创建会话
        :return:
        """
        self.ensure_one()
        client = dt.get_client(self, dt.get_dingtalk_config(self, self.company_id))
        user_list = self.check_employee_ding_id()
        try:
            result = client.post('chat/create', {
                'name': self.name,
                'owner': self.employee_id.ding_id,
                'useridlist': user_list,
                'showHistoryType': self.show_history_type,
                'searchable': self.searchable,
                'validationType': self.validation_type,
                'mentionAllAuthority': self.mention_all_authority,
                'chatBannedType': self.chat_banned_type,
                'managementType': self.management_ype,
            })
        except Exception as e:
            raise UserError(e)
        logging.info(">>>创建群会话结果{}".format(result))
        if result.get('errcode') == 0:
            self.write({'chat_id': result.get('chatid'), 'state': 'normal'})
            self.message_post(body=_("群会话已创建!群会话的ID:{}").format(result.get('chatid')), message_type='notification')
        else:
            raise UserError(result.get('errmsg'))

    def write_dingtalk_chat(self):
        """
        修改会话
        :return:
        """
        self.ensure_one()
        client = dt.get_client(self, dt.get_dingtalk_config(self, self.company_id))
        try:
            result = client.post('chat/update', {
                'chatid': self.chat_id,
                'name': self.name,
                'owner': self.employee_id.ding_id,
                'showHistoryType': self.show_history_type,
                'searchable': self.searchable,
                'validationType': self.validation_type,
                'mentionAllAuthority': self.mention_all_authority,
                'chatBannedType': self.chat_banned_type,
                'managementType': self.management_ype,
            })
        except Exception as e:
            raise UserError(e)
        logging.info(">>>更新群会话结果{}".format(result))
        if result.get('errcode') == 0:
            self.message_post(body="群会话已更新!", message_type='notification')
        else:
            raise UserError(result.get('errmsg'))

    def check_employee_ding_id(self):
        if not self.employee_id.ding_id:
            raise UserError(_("员工（群主）在钉钉中不存在，请选择其他人员!"))
        user_list = list()
        for emp in self.useridlist:
            if not emp.ding_id:
                raise UserError(_("员工{}:在钉钉中不存在，请选择其他人员!").format(emp.name))
            user_list.append(emp.ding_id)
        return user_list

    @api.model
    def process_dingtalk_chat(self, msg, company):
        """
        接受来自钉钉回调的处理
        :param msg: 回调消息
        :param company: 公司
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                domain = [('chat_id', '=', msg.get('ChatId')), ('company_id', '=', company.id)]
                chat = self.env['dingtalk.mc.chat'].with_user(SUPERUSER_ID).search(domain, limit=1)
                if not chat:
                    return
                # 群会话更换群主
                if msg.get('EventType') == 'chat_update_owner':
                    domain = [('ding_id', '=', msg.get('Owner')), ('company_id', '=', company.id)]
                    employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain, limit=1)
                    if employee:
                        chat.with_user(SUPERUSER_ID).write({'employee_id': employee.id})
                # 群会话更换群名称
                elif msg.get('EventType') == 'chat_update_title':
                    chat.with_user(SUPERUSER_ID).write({'name': msg.get('Title')})
                # 群会话添加人员
                elif msg.get('EventType') == 'chat_add_member':
                    new_users = list()
                    for user in chat.useridlist:
                        new_users.append(user.id)
                    for user in msg.get('UserId'):
                        domain = [('ding_id', '=', user), ('company_id', '=', company.id)]
                        employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain, limit=1)
                        if employee:
                            new_users.append(employee.id)
                    chat.with_user(SUPERUSER_ID).write({'useridlist': [(6, 0, new_users)]})
                # 群会话删除人员
                elif msg.get('EventType') == 'chat_remove_member':
                    for user in msg.get('UserId'):
                        domain = [('ding_id', '=', user), ('company_id', '=', company.id)]
                        employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain, limit=1)
                        if employee:
                            chat.with_user(SUPERUSER_ID).write({'useridlist': [(3, employee[0].id)]})
                # 群会话用户主动退群
                elif msg.get('EventType') == 'chat_quit':
                    domain = [('ding_id', '=', msg.get('Operator')), ('company_id', '=', company.id)]
                    employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain, limit=1)
                    if employee:
                        chat.with_user(SUPERUSER_ID).write({'useridlist': [(3, employee[0].id)]})
                # 群会话解散群
                elif msg.get('EventType') == 'chat_disband':
                    if chat:
                        domain = [('ding_id', '=', msg.get('Operator')), ('company_id', '=', company.id)]
                        emp = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain, limit=1)
                        chat.with_user(SUPERUSER_ID).write({'state': 'close'})
                        if emp:
                            chat.with_user(SUPERUSER_ID).message_post(body=_("群会话已被解散，操作人: {}!").format(emp[0].name), message_type='notification')
                return True

    def unlink(self):
        """
        删除
        :return:
        """
        for res in self:
            if res.state == 'normal':
                raise UserError('已在钉钉端建立群会话，不允许删除！')
        super(DingTalkMcChat, self).unlink()


class DingTalkChatUserModelAdd(models.TransientModel):
    _name = 'dingtalk.chat.user.model.add'
    _description = "群会话添加成员"

    on_user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingtalk_chat_on_user_add_and_hr_employee_rel',
                                   column1='model_id', column2='emp_id', string='已有成员')
    user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingtalk_chat_user_add_and_hr_employee_rel',
                                column1='model_id', column2='emp_id', string='新群成员', required=True)

    @api.onchange('on_user_ids')
    def _onchange_on_user_ids(self):
        """待添加人员下拉列表不显示当前群内成员
        """
        if self.on_user_ids:
            domain = [('id', 'not in', self.on_user_ids.ids)]
            return {
                'domain': {'user_ids': domain}
            }

    @api.model
    def default_get(self, _fields):
        res = super(DingTalkChatUserModelAdd, self).default_get(_fields)
        chat_id = self.env.context.get('active_id', False)
        ding_chat = self.env['dingtalk.mc.chat'].browse(chat_id)
        if 'on_user_ids' in _fields:
            res.update({'on_user_ids': [(6, 0, ding_chat.useridlist.ids)]})
        return res

    def add_chat_users(self):
        """
        添加群成员
        :return:
        """
        self.ensure_one()
        for res in self:
            chat_id = self.env.context.get('active_id', False)
            ding_chat = self.env['dingtalk.mc.chat'].browse(chat_id)
            user_list = list()
            for emp in res.user_ids:
                if not emp.ding_id:
                    raise UserError(_("员工{}: 在钉钉中不存在，请选择其他人员!").format(emp.name))
                user_list.append(emp.ding_id)
            chatid = ding_chat.chat_id
            add_useridlist = user_list
            try:
                client = dt.get_client(self, dt.get_dingtalk_config(self, ding_chat.company_id))
                result = client.chat.update(chatid, add_useridlist=add_useridlist)
                logging.info(">>>添加群成员返回结果%s", result)
                if result.get('errcode') == 0:
                    new_user_list = list()
                    for user in res.on_user_ids:
                        new_user_list.append(user.id)
                    for user in res.user_ids:
                        new_user_list.append(user.id)
                    ding_chat.write({'useridlist': [(6, 0, new_user_list)]})
                    ding_chat.message_post(
                        body=_("群成员已增加!"), message_type='notification')
                else:
                    raise UserError(_('群成员更新失败，详情为:{}').format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)


class DingTalkChatUserModelDel(models.TransientModel):
    _name = 'dingtalk.chat.user.model.del'
    _description = "群会话删除成员"

    user_ids = fields.Many2many(comodel_name='hr.employee', relation='dingtalk_chat_user_del_and_hr_employee_rel',
                                column1='model_id', column2='emp_id', string='删除群成员', required=True)
    old_user_ids = fields.Many2many(comodel_name='hr.employee',
                                    relation='dingtalk_chat_old_user_del_and_hr_employee_rel',
                                    column1='model_id', column2='emp_id', string='群成员', required=True)

    @api.onchange('old_user_ids')
    def _onchange_old_user_ids(self):
        """待删除人员下拉列表只显示当前群内成员
        """
        if self.old_user_ids:
            domain = [('id', 'in', self.old_user_ids.ids)]
            return {
                'domain': {'user_ids': domain}
            }

    @api.model
    def default_get(self, _fields):
        res = super(DingTalkChatUserModelDel, self).default_get(_fields)
        chat_id = self.env.context.get('active_id', False)
        ding_chat = self.env['dingtalk.mc.chat'].browse(chat_id)
        if 'old_user_ids' in _fields:
            res.update({'old_user_ids': [(6, 0, ding_chat.useridlist.ids)]})
        return res

    def del_chat_users(self):
        """
        删除群成员
        :return:
        """
        for res in self:
            chat_id = self.env.context.get('active_id', False)
            ding_chat = self.env['dingtalk.mc.chat'].browse(chat_id)
            user_list = list()
            for emp in res.user_ids:
                if not emp.ding_id:
                    raise UserError(_("员工{}:在钉钉中不存在，请选择其他人员!").format(emp.name))
                user_list.append(emp.ding_id)
            chatid = ding_chat.chat_id
            del_useridlist = user_list
            try:
                client = dt.get_client(self, dt.get_dingtalk_config(self, ding_chat.company_id))
                result = client.chat.update(chatid, del_useridlist=del_useridlist)
                logging.info(">>>删除群成员返回结果%s", result)
                if result.get('errcode') == 0:
                    for user in res.user_ids:
                        ding_chat.write({'useridlist': [(3, user.id)]})
                    ding_chat.message_post(body=_("群成员已删除!"), message_type='notification')
                else:
                    raise UserError(
                        _('群成员更新失败，详情为:{}').format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)

