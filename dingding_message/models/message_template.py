# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingMessageTemplateLine(models.Model):
    _name = 'dingding.message.template.line'
    _description = "消息模板列表"
    _rec_name = 'template_id'

    sequence = fields.Integer(string='序号')
    model_id = fields.Many2one(
        comodel_name='ir.model', string='Odoo模型', required=True)
    template_id = fields.Many2one(
        comodel_name='dingding.message.template', string='消息模板', ondelete='cascade')
    field_name = fields.Char(string='消息名称', required=True)
    field_id = fields.Many2one(
        comodel_name='ir.model.fields', string='取值字段', required=True)

    @api.onchange('model_id')
    def _onchange_model_id_onchange(self):
        model_id = self._context['model_id']
        if not model_id:
            raise UserError("请先选择模型！")
        for res in self:
            res.model_id = model_id
        return {
            'domain': {
                'field_id': [('model_id', '=', model_id),
                             ('ttype', 'in', ['char', 'date', 'float', 'integer', 'text', 'html', 'many2one'])]
            }
        }


class DingDingMessageTemplate(models.Model):
    _name = 'dingding.message.template'
    _description = "消息模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    model_id = fields.Many2one(
        comodel_name='ir.model', string='Odoo模型', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='公司',
                                 default=lambda self: self.env.user.company_id.id)
    create_send = fields.Boolean(string='创建时自动发送消息')
    delete_send = fields.Boolean(string='删除时自动发送消息')
    line_ids = fields.One2many(
        comodel_name='dingding.message.template.line', inverse_name='template_id', string='消息字段')
    msg_type = fields.Selection(string='接受者', selection=[('00', '员工'), ('01', '部门'), ('03', '所有人')],
                                required=True, default='00')
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_message_temp_and_employee_rel',
                               column1='template_id', column2='employee_id', string='员工',
                               domain=[('ding_id', '!=', '')])
    dept_ids = fields.Many2many(comodel_name='hr.department', relation='dingding_message_temp_and_department_rel',
                                column1='template_id', column2='department_id', string='部门',
                                domain=[('ding_id', '!=', '')])

    _sql_constraints = [
        ('model_id_uniq', 'unique (model_id)', 'Odoo模型已存在消息模板,请不要重复创建!'),
    ]

    @api.onchange('model_id')
    def _onchange_model(self):
        for res in self:
            if res.model_id:
                res.name = "{}-消息模板".format(res.model_id.name)

    def check_message_template(self, model, model_type):
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', model)]).id
        template = self.env['dingding.message.template'].sudo().search(
            [('model_id', '=', model_id)])
        if template:
            if model_type == 'create':
                return True if template.create_send else False
            elif model_type == 'delete':
                return True if template.delete_send else False
        else:
            return False

    def send_message_template(self, model, res_id, model_type):
        """发送消息"""
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', model)]).id
        template = self.env['dingding.message.template'].sudo().search(
            [('model_id', '=', model_id)])
        document = self.env[model].sudo().browse(res_id).copy_data()  # 当前单据
        message_dict = self.create_message_dict(
            model_type, template, document[0])
        logging.info(">>>msg:%s", message_dict)
        # 调用消息函数发送
        try:
            if template.msg_type == '03':
                self.env['dingding.work.message'].sudo().send_work_message(
                    toall=True, msg=message_dict)
            elif template.msg_type == '00':
                user_str = ''
                for user in template.emp_ids:
                    if user_str == '':
                        user_str = user_str + "{}".format(user.ding_id)
                    else:
                        user_str = user_str + ",{}".format(user.ding_id)
                self.env['dingding.work.message'].sudo().send_work_message(
                    userstr=user_str, msg=message_dict)
            elif template.msg_type == '01':
                dept_str = ''
                for dept in template.dept_ids:
                    if dept_str == '':
                        dept_str = dept_str + "{}".format(dept.ding_id)
                    else:
                        dept_str = dept_str + ",{}".format(dept.ding_id)
                self.env['dingding.work.message'].sudo().send_work_message(
                    deptstr=dept_str, msg=message_dict)
        except Exception as e:
            logging.info("发送消息失败!错误消息为:%s", e)

    def create_message_dict(self, model_type, template, res_dict):
        """
        封装为待发送消息的格式
        :param model_type:
        :param template:
        :param res_dict:
        :return: dict()
        """
        msg_text = ''
        if model_type == 'create':
            msg_text = "{}创建了'{}',内容:\n".format(
                self.env.user.name, template.model_id.name)
        elif model_type == 'delete':
            msg_text = "{}删除了'{}',内容:\n".format(
                self.env.user.name, template.model_id.name)
        for tem_line in template.line_ids:
            # 拼接消息字段
            if tem_line.field_id.ttype == 'many2one':
                doc_model = self.env[tem_line.field_id.relation].sudo().search(
                    [('id', '=', res_dict.get(tem_line.field_id.name))])
                if doc_model:
                    try:
                        msg_text = msg_text + \
                            "{}: {}\n".format(
                                tem_line.field_name, doc_model[0].name)
                    except Exception as e:
                        msg_text = msg_text + \
                            "{}: {}\n".format(tem_line.field_name, "字段值获取失败!")
            else:
                if res_dict.get(tem_line.field_id.name):
                    msg_text = msg_text + \
                        "{}: {}\n".format(tem_line.field_name,
                                          res_dict.get(tem_line.field_id.name))
                else:
                    msg_text = msg_text + \
                        "{}: {}\n".format(tem_line.field_name, "字段值获取失败!")
        return {
            'msgtype': 'text',
            "text": {
                "content": "{}请注意查看!".format(msg_text),
            }
        }
