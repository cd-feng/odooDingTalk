# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    ding_id = fields.Char(string='钉钉标签ID', index=True)
    ding_category_type = fields.Char(string='标签分类名')
    company_id = fields.Many2one('res.company', string='关联公司', default=lambda self: self.env.company)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    ding_id = fields.Char(string='钉钉ID', help="用于存储在钉钉系统中返回的联系人id", index=True)
    ding_company_name = fields.Char(string='钉钉联系人公司')
    ding_employee_id = fields.Many2one('hr.employee', string=u'钉钉负责人', ondelete='set null', domain=[('ding_id', '!=', '')])

    # def create_ding_partner(self):
    #     self.ensure_one()
    #     client = dingtalk_api.get_client()
    #     # 获取标签
    #     label_list = list()
    #     if self.category_id:
    #         for category in self.category_id:
    #             label_list.append(category.ding_id)
    #     else:
    #         raise UserError('请选择联系人标签，若不存在标签，请先使用手动同步联系人标签功能！')
    #     if not self.mobile and not self.phone:
    #         raise UserError('手机号码或电话为必填！')
    #     if not self.ding_employee_id:
    #         raise UserError("请选择联系人对应的负责人!")
    #     try:
    #         result = client.extcontact.create(self.name, self.ding_employee_id.ding_id, label_list, self.mobile, '86', self.function,
    #                                 (), self.comment, self.street, self.ding_company_name, ())
    #         self.ding_id = result
    #         self.message_post(body=u"已上传联系人信息至钉钉。*_*!", message_type='notification')
    #     except Exception as e:
    #         raise UserError(e)
    #     return {'type': 'ir.actions.act_window_close'}
    #
    # def update_ding_partner(self):
    #     """
    #     修改联系人时同步至钉钉
    #     :return:
    #     """
    #     self.ensure_one()
    #     client = dingtalk_api.get_client()
    #     # 获取标签
    #     label_list = list()
    #     if self.category_id:
    #         for category in self.category_id:
    #             label_list.append(category.ding_id)
    #     else:
    #         raise UserError('请选择联系人标签，若不存在标签，请先使用手动同步联系人标签功能！')
    #     if not self.ding_employee_id:
    #         raise UserError("请选择联系人对应的负责人!")
    #     try:
    #         client.extcontact.update(self.ding_id, self.name, self.ding_employee_id.ding_id, label_list, self.mobile, '86',
    #                                           self.function, (), self.comment, self.street, self.ding_company_name, ())
    #         self.message_post(body=u"已更新联系人信息至钉钉。*_*!", message_type='notification')
    #     except Exception as e:
    #         raise UserError(e)
    #     return {'type': 'ir.actions.act_window_close'}
    #
    # def delete_ding_partner(self):
    #     """
    #     删除联系人
    #     :return:
    #     """
    #     for res in self:
    #         if not res.ding_id:
    #             continue
    #         self._delete_dingtalk_partner_by_id(res.ding_id)
    #         res.write({'ding_id': False})
    #         res.message_post(body=u"已成功在钉钉上删除联系人。*_*!", message_type='notification')
    #     return {'type': 'ir.actions.act_window_close'}
    #
    # def _delete_dingtalk_partner_by_id(self, ding_id):
    #     client = dingtalk_api.get_client()
    #     try:
    #         result = client.extcontact.delete(ding_id)
    #         _logger.info(_("已在钉钉上删除Id:{}的联系人".format(result)))
    #     except Exception as e:
    #         raise UserError(e)
    #     return
    #
    # def unlink(self):
    #     for res in self:
    #         if res.ding_id and dingtalk_api.get_delete_is_synchronous():
    #             self._delete_dingtalk_partner_by_id(res.ding_id)
    #         return super(ResPartner, self).unlink()