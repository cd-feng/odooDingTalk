# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

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

    ding_id = fields.Char(string='钉钉Id', index=True)
    din_sy_state = fields.Boolean(string=u'钉钉同步标识', default=False, help="避免使用同步时,会执行创建、修改上传钉钉方法")
    dingding_type = fields.Selection(string=u'钉钉状态', selection=[('no', '不存在'), ('yes', '存在')], compute="_compute_dingding_type")
    child_ids = fields.One2many(comodel_name='hr.department', inverse_name='parent_id', string=u'下级部门')
    manager_user_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_department_managr_user_employee_rel', string=u'主管')

    
    def create_ding_department(self):
        for res in self:
            if res.ding_id:
                raise UserError("该部门已在钉钉中存在！")
            url, token = self.env['dingding.parameter'].get_parameter_value_and_token('department_create')
            data = {'name': res.name}  # 部门名称
            # 获取父部门ding_id
            if res.parent_id:
                data.update({'parentid': res.parent_id.ding_id if res.parent_id.ding_id else ''})
            else:
                raise UserError("请选择上级部门!")
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=10)
                result = json.loads(result.text)
                logging.info(">>>新增部门返回结果:{}".format(result))
                if result.get('errcode') == 0:
                    res.write({'ding_id': result.get('id')})
                    res.message_post(body=u"钉钉消息：部门信息已上传至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传至钉钉网络超时！")

    
    def update_ding_department(self):
        for res in self:
            url = self.env['dingding.parameter'].search([('key', '=', 'department_update')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            # 获取部门ding_id
            if not res.parent_id:
                raise UserError("请选择上级部门!")
            data = {
                'id': res.ding_id,  # id
                'name': res.name,  # 部门名称
                'parentid': res.parent_id.ding_id,  # 父部门id
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=10)
                result = json.loads(result.text)
                logging.info(">>>修改部门时钉钉返回结果:{}".format(result))
                if result.get('errcode') == 0:
                    res.message_post(body=u"钉钉消息：新的信息已同步更新至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传至钉钉超时！")

    # 重写删除方法
    
    def unlink(self):
        for res in self:
            ding_id = res.ding_id
            super(HrDepartment, self).unlink()
            din_delete_department = self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_delete_department')
            if din_delete_department:
                self.delete_din_department(ding_id)
            return True

    @api.model
    def delete_din_department(self, ding_id):
        """删除钉钉部门"""
        url = self.env['dingding.parameter'].search([('key', '=', 'department_delete')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        data = {
            'id': ding_id,  # userid
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=15)
            result = json.loads(result.text)
            logging.info(">>>删除钉钉部门返回结果:{}".format(result))
            if result.get('errcode') != 0:
                raise UserError('删除钉钉部门时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("同步至钉钉超时！")

    def _compute_dingding_type(self):
        for res in self:
            res.dingding_type = 'yes' if res.ding_id else 'no'

