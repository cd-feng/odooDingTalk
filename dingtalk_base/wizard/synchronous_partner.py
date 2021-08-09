# -*- coding: utf-8 -*-

import logging
import threading
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt
_logger = logging.getLogger(__name__)

SYNCHRONOUSDINGTALKPARTNER = False


class SynchronousPartner(models.TransientModel):
    _name = 'dingtalk.synchronous.partner'
    _description = '联系人同步'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]

    company_ids = fields.Many2many('res.company', 'dingtalk_synchronous_partner_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.user.company_id.id])])
    repeat_type = fields.Selection(string=u'主键判断', selection=RepeatType, default='id')

    def on_synchronous(self):
        """
        同步联系人信息
        :return:
        """
        self.ensure_one()
        global SYNCHRONOUSDINGTALKPARTNER
        if SYNCHRONOUSDINGTALKPARTNER:
            raise exceptions.UserError('系统正在后台同步联系人信息，请勿再次发起！')
        SYNCHRONOUSDINGTALKPARTNER = True  # 变为正在同步
        # 当前操作用户
        user_id = self.env.user.id
        t = threading.Thread(target=self._synchronous_partner, args=(user_id, self.company_ids.ids))
        t.start()
        return self.env.user.notify_success(message="系统正在后台同步联系人信息，请耐心等待处理完成...")

    def _synchronous_partner(self, user_id, company_ids):
        """
        异步处理同步联系人信息
        :return:
        """
        global SYNCHRONOUSDINGTALKPARTNER
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                start_time = datetime.now()  # 开始的时间
                user = self.env['res.users'].sudo().search([('id', '=', user_id)])
                for company_id in company_ids:
                    company = self.env['res.company'].sudo().search([('id', '=', company_id)], limit=1)
                    # 同步联系人标签
                    self._synchronous_partner_category(company, user)
                    # 同步联系人
                    self._synchronous_partner_list(company, user)
                SYNCHRONOUSDINGTALKPARTNER = False
                end_time = datetime.now()
                res_str = "同步钉钉联系人完成，共用时：{}秒".format((end_time - start_time).seconds)
                _logger.info(res_str)
                return user.sudo().notify_success(message=res_str, sticky=True)

    def _synchronous_partner_category(self, company, user):
        """
        同步联系人标签
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            results = client.ext.listlabelgroups()
            category_list = list()
            for res in results:
                for labels in res.get('labels'):
                    category_list.append({
                        'name': labels.get('name'),
                        'ding_id': labels.get('id'),
                        'ding_category_type': res.get('name'),
                        'company_id': company.id,
                    })
            for category in category_list:
                res_category = self.env['res.partner.category'].sudo().search(
                    [('ding_id', '=', category.get('ding_id')), ('company_id', '=', company.id)])
                if res_category:
                    res_category.sudo().write(category)
                else:
                    self.env['res.partner.category'].sudo().create(category)
        except Exception as e:
            error_str = "同步联系人标签失败，原因：{}".format(str(e))
            return user.sudo().notify_success(message=error_str, sticky=True)

    def _synchronous_partner_list(self, company, user):
        """
        同步联系人列表
        :param company:
        :param user:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            results = client.ext.list(offset=0, size=100)
            for res in results:
                # 获取标签
                label_list = list()
                for label in res.get('labelIds'):
                    cat_domain = [('ding_id', '=', label), ('company_id', '=', company.id)]
                    category = self.env['res.partner.category'].sudo().search(cat_domain, limit=1)
                    if category:
                        label_list.append(category.id)
                data = {
                    'name': res.get('name'),
                    'function': res.get('title'),
                    'category_id': [(6, 0, label_list)],  # 标签
                    'ding_id': res.get('userId'),  # 钉钉用户id
                    'comment': res.get('remark'),  # 备注
                    'street': res.get('address'),  # 地址
                    'mobile': res.get('mobile'),  # 手机
                    'phone': res.get('mobile'),  # 电话
                    'ding_company_name': res.get('company_name'),  # 钉钉公司名称
                    'company_id': company.id
                }
                # 获取负责人
                if res.get('followerUserId'):
                    emp_domain = [('ding_id', '=', res.get('followerUserId')), ('company_id', '=', company.id)]
                    follower_user = self.env['hr.employee'].sudo().search(emp_domain, limit=1)
                    if follower_user:
                        data.update({'ding_employee_id': follower_user.id})
                partner_domain = [('ding_id', '=', res.get('userId')), ('company_id', '=', company.id)]
                partner = self.env['res.partner'].sudo().search(partner_domain)
                if partner:
                    partner.sudo().write(data)
                else:
                    self.env['res.partner'].sudo().create(data)
        except Exception as e:
            error_str = "同步联系人失败，原因：{}".format(str(e))
            return user.sudo().notify_success(message=error_str, sticky=True)

