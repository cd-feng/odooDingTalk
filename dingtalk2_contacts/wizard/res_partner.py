# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import api, fields, models, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class SyncPartner(models.TransientModel):
    _name = 'dingtalk2.syn.partner'
    _description = '联系人同步'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]
    company_ids = fields.Many2many('res.company', 'dingtalk_synchronous_partner_rel', string="公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.company.id])])
    repeat_type = fields.Selection(string='主键判断', selection=RepeatType, default='name')

    def on_synchronous(self):
        """
        开始同步联系人
        """
        start_time = datetime.now()  # 开始的时间
        for company_id in self.company_ids:
            client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
            try:
                results = client.ext.list(offset=0, size=100)
            except Exception as e:
                raise exceptions.UserError("同步联系人失败，原因：{}".format(str(e)))
            for res in results:
                value = {
                    'function': res.get('title'),
                    'comment': res.get('remark'),
                    'street': res.get('address'),
                    'name': res.get('name'),
                    'mobile': res.get('mobile'),
                    'phone': res.get('mobile'),
                    'ding_id': res.get('userId'),
                    'email': res.get('email'),
                    'ding_company_name': res.get('companyName'),  # 钉钉公司名称
                    'company_id': company_id.id
                }
                if res.get('followerUserId'):      # 获取负责人
                    emp_domain = [('ding_id', '=', res.get('followerUserId')), ('company_id', '=', company_id.id)]
                    follower_user = self.env['hr.employee'].sudo().search(emp_domain, limit=1)
                    if follower_user:
                        value['ding_employee_id'] = follower_user.id
                if self.repeat_type == 'name':
                    partner_domain = [('name', '=', res.get('name')), ('company_id', '=', company_id.id)]
                else:
                    partner_domain = [('ding_id', '=', res.get('userId')), ('company_id', '=', company_id.id)]
                partner = self.env['res.partner'].search(partner_domain)
                if partner:
                    partner.write(value)
                else:
                    self.env['res.partner'].create(value)
        end_time = datetime.now()
        _logger.debug("同步联系人列表完成，共用时：{}秒".format((end_time - start_time).seconds))

