# -*- coding: utf-8 -*-
from odoo import models, fields, api
import random
import string


class DingTalkConfig(models.Model):
    _name = 'dingtalk.config'
    _description = "参数配置"
    _rec_name = 'name'

    @api.model
    def _get_default_aes_key(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 43))

    @api.model
    def _get_default_token(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 25))

    company_id = fields.Many2one('res.company', string='关联公司', default=lambda self: self.env.company, index=True)
    name = fields.Char(string='钉钉企业名称', index=True, required=True)
    agent_id = fields.Char(string=u'AgentId')
    corp_id = fields.Char(string=u'CorpId')
    app_key = fields.Char(string=u'AppKey')
    app_secret = fields.Char(string=u'AppSecret')
    login_id = fields.Char(string=u'登录AppId')
    login_secret = fields.Char(string=u'登录AppSecret')
    m_login = fields.Boolean(string=u'开启免登?')
    delete_is_sy = fields.Boolean(string=u'同步删除员工?', help="删除odoo员工时同步推送到钉钉")
    is_auto_create_user = fields.Boolean(string="自动创建系统用户？",
                                         help='开启自动创建系统用户后，系统将会在收到钉钉回调通知后，立即创建一个属于该员工的系统用户！')

    encrypt_aes_key = fields.Char(string="订阅加密AesKey", default=_get_default_aes_key)
    encrypt_token = fields.Char(string="订阅签名Token", default=_get_default_token)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', '钉钉企业名称已存在，请更换！'),
        ('company_id_uniq', 'UNIQUE (company_id)', '该企业对应的公司存在，请更换！'),
    ]

    def set_default_user_groups(self):
        """
        设置默认系统用户权限
        :return:
        """
        action = self.env.ref('base.action_res_users').read()[0]
        action['res_id'] = self.env.ref('base.default_user').id
        action['views'] = [[self.env.ref('base.view_users_form').id, 'form']]
        return action
