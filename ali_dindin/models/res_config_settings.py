# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    din_agentid = fields.Char(string=u'AgentId')
    din_appkey = fields.Char(string=u'AppKey')
    din_appsecret = fields.Char(string=u'AppSecret')
    din_token = fields.Boolean(string="自动获取Token")
    din_create_extcontact = fields.Boolean(string=u'添加外部联系人')
    din_update_extcontact = fields.Boolean(string=u'修改外部联系人')
    din_delete_extcontact = fields.Boolean(string=u'删除外部联系人')
    din_create_employee = fields.Boolean(string=u'添加员工')
    din_update_employee = fields.Boolean(string=u'修改员工')
    din_delete_employee = fields.Boolean(string=u'删除员工')
    din_create_department = fields.Boolean(string=u'添加部门')
    din_update_department = fields.Boolean(string=u'修改部门')
    din_delete_department = fields.Boolean(string=u'删除部门')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            din_agentid=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_agentid'),
            din_appkey=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appkey'),
            din_appsecret=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appsecret'),
            din_token=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_token'),
            din_create_extcontact=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_create_extcontact'),
            din_update_extcontact=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_update_extcontact'),
            din_delete_extcontact=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_extcontact'),
            din_create_employee=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_create_employee'),
            din_update_employee=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_update_employee'),
            din_delete_employee=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_employee'),
            din_create_department=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_create_department'),
            din_update_department=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_update_department'),
            din_delete_department=self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_department'),
        )
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_agentid', self.din_agentid)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_appkey', self.din_appkey)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_appsecret', self.din_appsecret)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_token', self.din_token)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_create_extcontact', self.din_create_extcontact)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_update_extcontact', self.din_update_extcontact)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_delete_extcontact', self.din_delete_extcontact)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_create_employee', self.din_create_employee)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_update_employee', self.din_update_employee)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_delete_employee', self.din_delete_employee)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_create_department', self.din_create_department)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_update_department', self.din_update_department)
        self.env['ir.config_parameter'].sudo().set_param('ali_dindin.din_delete_department', self.din_delete_department)
        super(ResConfigSettings, self).set_values()
        data = {
            'name': '钉钉-定时更新token值',
            'active': True,
            'model_id': self.env['ir.model'].sudo().search([('model', '=', 'ali.dindin.get.token')]).id,
            'state': 'code',
            'user_id': self.env.user.id,
            'numbercall': -1,
            'interval_number': 30,
            'interval_type': 'minutes',
            'code': "env['ali.dindin.get.token'].get_token()",
        }
        if self.auto_token:
            cron = self.env['ir.cron'].sudo().search([('code', '=', "env['ali.dindin.get.token'].get_token()")])
            if len(cron) >= 1:
                cron.sudo().write(data)
            else:
                self.env['ir.cron'].sudo().create(data)
        else:
            cron = self.env['ir.cron'].sudo().search(
                [('code', '=', "env['ali.dindin.get.token'].get_token()")])
            cron.sudo().unlink()


class UnionPayConfig(models.Model):
    _description = '系统参数列表'
    _name = 'ali.dindin.system.conf'

    name = fields.Char(string='名称')
    key = fields.Char(string='key值')
    value = fields.Char(string='参数值')
    state = fields.Selection(string=u'有效', selection=[('y', '是'), ('n', '否'), ], default='y')

