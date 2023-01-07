# -*- coding: utf-8 -*-
import logging
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt

_logger = logging.getLogger(__name__)


class DingTalkApprovalTemplateTran(models.TransientModel):
    _name = 'dingtalk.approval.template.tran'
    _description = "获取审批模板"

    company_ids = fields.Many2many("res.company", string="选择公司", required=True, default=lambda self: self.env.company)

    def get_template(self):
        """
        获取审批模板
        :return:
        """
        self.ensure_one()
        template_model = self.env['dingtalk.approval.template']
        for company in self.company_ids:
            company_id = company.id
            client = dt.get_client(self, dt.get_dingtalk2_config(self, company))
            offset = 0
            size = 100
            while True:
                try:
                    result = client.post('topapi/process/listbyuserid', {'offset': offset, 'size': size})
                except Exception as e:
                    raise UserError(e)
                if result.get('errcode') == 0:
                    result = result.get('result')
                    for process in result.get('process_list'):
                        data = {
                            'name': process.get('name'),
                            'icon_avatar_url': process.get('icon_url'),
                            'process_code': process.get('process_code'),
                            'url': process.get('url'),
                            'company_id': company_id,
                        }
                        domain = [('company_id', '=', company_id), ('process_code', '=', process.get('process_code'))]
                        template = template_model.search(domain)
                        if template:
                            template.write(data)
                        else:
                            template_model.create(data)
                    if result.get('next_cursor'):
                        offset += result.get('next_cursor')
                    else:
                        break
                else:
                    raise UserError('获取审批模板失败，详情为:{}'.format(result.get('errmsg')))
        _logger.info('已获取钉钉端所有审批模板！')
        return {'type': 'ir.actions.act_window_close'}

