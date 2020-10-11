# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingtalkMicroapp(models.Model):
    _description = "应用列表"
    _name = 'dingtalk.miroapp.list'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="应用名称", required=True)
    icon_url = fields.Html(string='图标', compute='_compute_icon_url')
    icon_avatar_url = fields.Text(string='图标url')
    agent_id = fields.Char(string="实例化Id", required=True)
    app_desc = fields.Text(string="应用描述")
    is_self = fields.Selection(string="自建应用", selection=[('y', '是'), ('n', '否')])
    home_link = fields.Char(string="移动端主页")
    pc_link = fields.Char(string="PC端主页")
    state = fields.Selection(string="状态", selection=[('1', '启用'), ('0', '停用'), ('3', '未知')])
    oa_link = fields.Char(string="OA后台管理主页")
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id)
    is_hidden = fields.Boolean(string="管理员可见？")
    department_ids = fields.Many2many(comodel_name="hr.department", relation="miroapp_list_and_department_rel", string="可见部门")
    employee_ids = fields.Many2many(comodel_name="hr.employee", relation="miroapp_list_and_employee_rel", string="可见员工")

    @api.depends('icon_avatar_url')
    def _compute_icon_url(self):
        for res in self:
            if res.icon_avatar_url:
                res.icon_url = """<img src="{avatar_url}" width="60px" height="60px">""".format(avatar_url=res.icon_avatar_url)
            else:
                res.icon_url = False

    def get_visible_scopes(self):
        """
        获取应用的可见范围
        :return:
        """
        for res in self:
            client = dt.get_client(res, dt.get_dingtalk_config(res, res.company_id))
            try:
                result = client.post('microapp/visible_scopes', {'agentId': res.agent_id})
            except Exception as e:
                raise UserError(e)
            if result.get('errcode') == 0:
                # 获取当前公司下的所有本部门列表
                dept_dict = dict()
                departments = self.env['hr.department'].with_user(SUPERUSER_ID).search([('company_id', '=', res.company_id.id), ('ding_id', '!=', '')])
                for dept in departments:
                    dept_dict[dept.ding_id] = dept.id
                # 获取所有员工
                emp_dict = dict()
                emps = self.env['hr.employee'].with_user(SUPERUSER_ID).search([('company_id', '=', res.company_id.id), ('ding_id', '!=', '')])
                for emp in emps:
                    emp_dict[emp.ding_id] = emp.id
                is_hidden = result.get('isHidden')
                user_list = list()
                dept_list = list()
                try:
                    for dept in result.get('deptVisibleScopes'):
                        if dept_dict.get(dept):
                            dept_list.append(dept_dict.get(dept))
                    for user_id in result.get('userVisibleScopes'):
                        if emp_dict.get(user_id):
                            user_list.append(emp_dict.get(user_id))
                except Exception as e:
                    msg = '获取应用:{} 的可见列表数据错误！{}; 错误:{}'.format(res.name, result, str(e))
                    _logger.info(msg)
                    res.message_post(body=msg, message_type='notification')
                res.write({
                    'is_hidden': is_hidden,
                    'department_ids': [(6, 0, dept_list)],
                    'employee_ids': [(6, 0, user_list)],
                })
            else:
                raise UserError('获取应用的可见范围失败，详情为:{}'.format(result.get('errmsg')))

