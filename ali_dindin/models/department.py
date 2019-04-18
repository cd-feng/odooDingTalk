# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

""" 钉钉部门功能模块 """


# 拓展部门
class HrDepartment(models.Model):
    _inherit = 'hr.department'

    din_id = fields.Char(string='钉钉Id')
    din_sy_state = fields.Boolean(string=u'钉钉同步标识', default=False, help="避免使用同步时,会执行创建、修改上传钉钉方法")

    @api.multi
    def create_din_department(self, values):
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'department_create')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        # 获取父部门din_id
        parent_id = False
        if values.get('parent_id'):
            department = self.env['hr.department'].sudo().search([('id', '=', values.get('parent_id'))])
            parent_id = department[0].din_id if department[0].din_id else ''
        else:
            raise UserError("请选择上级部门!")
        data = {
            'name': values.get('name'),  # 部门名称
            'parentid': parent_id,  # 父部门id
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(">>>新增部门返回结果:{}".format(result))
            if result.get('errcode') == 0:
                return result.get('id')
            else:
                raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传至钉钉超时！")

    @api.multi
    def update_din_department(self, department):
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'department_update')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        # 获取部门din_id
        if department.parent_id:
            dep = self.env['hr.department'].sudo().search([('id', '=', department.parent_id.id)])
            parent_id = dep[0].din_id if dep[0].din_id else ''
        else:
            raise UserError("请选择上级部门!")
        data = {
            'id': department.din_id,  # id
            'name': department.name,  # 部门名称
            'parentid': parent_id,  # 父部门id
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                   timeout=20)
            result = json.loads(result.text)
            logging.info(">>>修改部门时钉钉返回结果:{}".format(result))
            if result.get('errcode') == 0:
                department.message_post(body=u"修改信息已同步更新至钉钉", message_type='notification')
            else:
                raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传至钉钉超时！")

    # 重写删除方法
    @api.multi
    def unlink(self):
        din_id = self.din_id
        super(HrDepartment, self).unlink()
        din_delete_department = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_department')
        if din_delete_department:
            self.delete_din_department(din_id)
        return True

    @api.model
    def delete_din_department(self, din_id):
        """删除钉钉部门"""
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'department_delete')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'id': din_id,  # userid
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=15)
            result = json.loads(result.text)
            logging.info(">>>删除钉钉部门返回结果:{}".format(result))
            if result.get('errcode') != 0:
                raise UserError('删除钉钉部门时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("同步至钉钉超时！")

    # 同步钉钉部门数据
    @api.model
    def synchronous_dingding_department(self):
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'department_list')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {'id': 1}
        result = requests.get(url="{}{}".format(url, token), params=data, timeout=15)
        logging.info(">>>获取钉钉部门结果:{}".format(result.text))
        result = json.loads(result.text)
        if result.get('errcode') == 0:
            for res in result.get('department'):
                data = {
                    'name': res.get('name'),
                    'din_id': res.get('id'),
                }
                if res.get('parentid') != 1:
                    partner_department = self.env['hr.department'].search([('din_id', '=', res.get('parentid'))])
                    if partner_department:
                        data.update({'parent_id': partner_department[0].id})
                h_department = self.env['hr.department'].search([('din_id', '=', res.get('id'))])
                if h_department:
                    h_department.sudo().write(data)
                else:
                    self.env['hr.department'].create(data)
            return {'state': True}
        else:
            logging.info(">>>获取部门失败，原因为:{}".format(result.get('errmsg')))
            return {'state': False, 'msg': "获取部门失败，原因为:{}".format(result.get('errmsg'))}


# 同步钉钉部门功能模型
class DinDinSynchronousDepartment(models.TransientModel):
    _name = 'dindin.synchronous.department'
    _description = "同步钉钉部门功能模型"


