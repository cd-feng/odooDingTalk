# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# 继承联系人标签模型，增加钉钉返回的id、颜色字段
class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    din_id = fields.Char(string='钉钉标签ID')
    din_color = fields.Char(string='钉钉标签颜色')
    din_category_type = fields.Char(string='标签分类名')


# 继承联系人模型，增加钉钉返回的userid等字段
class ResPartner(models.Model):
    _inherit = 'res.partner'

    din_userid = fields.Char(string='钉钉联系人ID', help="用于存储在钉钉系统中返回的联系人id")
    din_company_name = fields.Char(string='钉钉联系人公司', help="用于存储在钉钉系统中返回的联系人id")
    din_sy_state = fields.Boolean(string=u'钉钉同步标识', default=False, help="避免使用同步时,会执行创建、修改上传钉钉方法")
    din_employee_id = fields.Many2one(comodel_name='hr.employee', string=u'负责人', ondelete='cascade')

    @api.multi
    def create_ding_partner(self):
        for res in self:
            if res.din_userid:
                raise UserError('钉钉中已存在该联系人,请不要重复上传或使用更新联系人功能！')
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'extcontact_create')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            # 获取标签
            label_list = list()
            if res.category_id:
                for category in res.category_id:
                    label_list.append(category.din_id)
            else:
                raise UserError('请选择联系人标签，若不存在标签，请先使用手动同步联系人标签功能！')
            if not res.mobile and not res.phone:
                raise UserError('手机号码或电话为必填！')
            if not res.din_employee_id:
                raise UserError("请选择联系人对应的负责人!")
            data = {
                'contact': {
                    'title': res.function,  # 职位
                    'label_ids': label_list,  # 标签列表
                    'address': res.street,  # 地址
                    'remark': res.comment,  # 备注
                    'follower_user_id': res.din_employee_id.din_id if res.din_employee_id else '',  # 负责人userid
                    'name': res.name,  # 联系人名称
                    'state_code': '86',  # 手机号国家码
                    'company_name': res.din_company_name,  # 钉钉企业公司名称
                    'mobile': res.mobile if res.mobile else res.phone,  # 手机
                }
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    res.write({'din_userid': result.get('userid')})
                    res.message_post(body=u"钉钉消息：联系人信息已上传至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传联系人至钉钉超时！")

    @api.multi
    def update_ding_partner(self):
        """修改员工时同步至钉钉"""
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'extcontact_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            # 获取标签
            label_list = list()
            if res.category_id:
                for label in res.category_id:
                    label_list.append(label.din_id)
            else:
                raise UserError('请选择联系人标签，若不存在标签，请先使用手动同步联系人标签功能！')
            if not res.din_employee_id:
                raise UserError("请选择联系人对应的负责人!")
            employee = self.env['hr.employee'].sudo().search([('id', '=', res.din_employee_id.id)])
            data = {
                'contact': {
                    'user_id': res.din_userid,  # 联系人钉钉id
                    'title': res.function,  # 职位
                    'label_ids': label_list,  # 标签列表
                    'address': res.street,  # 地址
                    'remark': res.comment,  # 备注
                    'follower_user_id': employee.din_id if employee else '',  # 负责人userid
                    'name': res.name,  # 联系人名称
                    'state_code': '86',  # 手机号国家码
                    'company_name': res.din_company_name,  # 钉钉企业公司名称
                    'mobile': res.mobile if res.mobile else res.phone,  # 手机
                }
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=20)
                result = json.loads(result.text)
                logging.info("更新联系人返回结果:{}".format(result))
                if result.get('errcode') == 0:
                    res.message_post(body=u"新的信息已同步更新至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传联系人至钉钉超时！")

    # 重写删除方法
    @api.multi
    def unlink(self):
        for res in self:
            din_userid = res.din_userid
            super(ResPartner, self).unlink()
            if self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_extcontact'):
                self.delete_din_extcontact(din_userid)
            return True

    @api.model
    def delete_din_extcontact(self, din_userid):
        """删除钉钉联系人"""
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'extcontact_delete')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'user_id': din_userid,  # din_userid
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
            result = json.loads(result.text)
            logging.info("删除钉钉联系人结果:{}".format(result))
            if result.get('errcode') != 0:
                raise UserError('删除钉钉联系人时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传至钉钉超时！")


# 未使用，但是不能删除，因为第一个版本创建的视图还存在
class DinDinSynchronous(models.TransientModel):
    _name = 'dindin.synchronous.extcontact'
    _description = "同步钉钉联系人功能模块"

    sy_type = fields.Selection(string=u'同步类型', selection=[('00', '联系人标签'), ('01', '外部联系人列表')], default='00')
