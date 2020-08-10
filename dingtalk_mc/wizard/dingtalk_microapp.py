# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingtalkMicroappWizard(models.TransientModel):
    _name = 'dingtalk.miroapp.list.wizard'
    _description = "获取应用列表向导"

    company_ids = fields.Many2many("res.company", string="选择公司", required=True)

    def get_miroapp_list(self):
        """
        获取审批模板
        :return:
        """
        self.ensure_one()
        for company in self.company_ids:
            company_id = company.id
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            try:
                result = client.post('microapp/list', {})
            except Exception as e:
                raise UserError(e)
            if result.get('errcode') == 0:
                for app in result.get('appList'):
                    data = {
                        'name': app.get('name'),
                        'icon_avatar_url': app.get('appIcon'),
                        'agent_id': app.get('agentId'),
                        'app_desc': app.get('appDesc'),
                        'is_self': 'y' if app.get('isSelf') else 'n',
                        'home_link': app.get('homepageLink'),
                        'pc_link': app.get('pcHomepageLink'),
                        'state': str(app.get('appStatus')),
                        'oa_link': app.get('ompLink'),
                        'company_id': company_id,
                    }
                    domain = [('company_id', '=', company_id), ('agent_id', '=', app.get('agentId'))]
                    miroapps = self.env['dingtalk.miroapp.list'].search(domain)
                    if miroapps:
                        miroapps.write(data)
                    else:
                        miroapps = self.env['dingtalk.miroapp.list'].create(data)
                    miroapps.get_visible_scopes()
                else:
                    break
            else:
                raise UserError('获取审批模板失败，详情为:{}'.format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}


class DingtalkSetMicroappVisibleWizard(models.TransientModel):
    _name = 'dingtalk.miroapp.set.visible.scopes'
    _description = '设置可见范围'
    
    miroapp_id = fields.Many2one(comodel_name="dingtalk.miroapp.list", string="应用")

    department_ids = fields.Many2many(comodel_name="hr.department", relation="miroapp_wizard_and_department_rel",
                                      string="可见部门", domain="[('ding_id', '!=', '')]")
    employee_ids = fields.Many2many(comodel_name="hr.employee", relation="miroapp_wizard_and_employee_rel",
                                    string="可见员工", domain="[('ding_id', '!=', '')]")
    is_hidden = fields.Boolean(string="管理员可见？")

    @api.model
    def default_get(self, _fields):
        res = super(DingtalkSetMicroappVisibleWizard, self).default_get(_fields)
        active_id = self.env.context.get('active_id', False)
        miroapp = self.env['dingtalk.miroapp.list'].browse(active_id)
        if miroapp:
            res.update({
                'department_ids': [(6, 0, miroapp.department_ids.ids)],
                'employee_ids': [(6, 0, miroapp.employee_ids.ids)],
                'is_hidden': miroapp.is_hidden
            })
        return res

    def set_visible_scopes(self):
        """
        设置可见范围
        :return:
        """
        self.ensure_one()
        miroapp_id = self.miroapp_id
        client = dt.get_client(self, dt.get_dingtalk_config(self, miroapp_id.company_id))
        user_list = list()
        dept_list = list()
        for user in self.employee_ids:
            user_list.append(user.ding_id)
        for dept in self.department_ids:
            dept_list.append(dept.ding_id)
        try:
            result = client.post('microapp/set_visible_scopes', {
                'agentId': miroapp_id.agent_id,
                'isHidden': self.is_hidden,
                'deptVisibleScopes': dept_list,
                'userVisibleScopes': user_list,
            })
        except Exception as e:
            raise UserError(e)
        if result.get('errcode') == 0:
            miroapp_id.write({
                'is_hidden': self.is_hidden,
                'department_ids': [(6, 0, self.department_ids.ids)],
                'employee_ids': [(6, 0, self.employee_ids.ids)],
            })
            miroapp_id.message_post(body=_("可见范围更新成功！"), message_type='notification')
        else:
            raise UserError(result.get('errmsg'))
