# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import base64
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    OfficeStatus = [
        ('2', '试用期'), ('3', '正式'), ('5', '待离职'), ('-1', '无状态')
    ]

    ding_id = fields.Char(string='钉钉Id', index=True)
    din_unionid = fields.Char(string='Union标识', index=True)
    din_jobnumber = fields.Char(string='员工工号')
    ding_avatar = fields.Html('钉钉头像', compute='_compute_ding_avatar')
    ding_avatar_url = fields.Char('头像url')
    din_hiredDate = fields.Date(string='入职时间')
    din_isAdmin = fields.Boolean("是管理员", default=False)
    din_isBoss = fields.Boolean("是老板", default=False)
    din_isLeader = fields.Boolean("是部门主管", default=False)
    din_isHide = fields.Boolean("隐藏手机号", default=False)
    din_isSenior = fields.Boolean("高管模式", default=False)
    din_active = fields.Boolean("是否激活", default=True)
    din_orderInDepts = fields.Char("所在部门序位")
    din_isLeaderInDepts = fields.Char("是否为部门主管")
    work_status = fields.Selection(string=u'入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')], default='2')
    office_status = fields.Selection(string=u'在职子状态', selection=OfficeStatus, default='-1')
    department_ids = fields.Many2many('hr.department', 'employee_department2_rel', string='所属部门')

    @api.depends('ding_avatar_url')
    def _compute_ding_avatar(self):
        for res in self:
            if res.ding_avatar_url:
                res.ding_avatar = """
                <img src="{avatar_url}" style="width:150px; height=150px;">""".format(avatar_url=res.ding_avatar_url)
            else:
                res.ding_avatar = False

    def create_ding_employee(self):
        """
        上传员工到钉钉
        :return:
        """
        for res in self:
            client = dingtalk_api.get_client()
            # 获取部门ding_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            elif res.department_ids:
                department_list = res.department_ids.mapped('ding_id')
                department_list.append(res.department_id.ding_id)
            else:
                department_list.append(res.department_id.ding_id)
            data = {
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else res.work_phone,  # 手机
                'tel': res.work_phone if res.work_phone else res.mobile_phone,  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
                'hiredDate': dingtalk_api.date_to_stamp(res.din_hiredDate) if res.din_hiredDate else '',  # 入职日期
            }
            try:
                result = client.user.create(data)
                res.write({'ding_id': result})
                res.message_post(body=u"已成功上传至钉钉", message_type='notification')
            except Exception as e:
                raise UserError(e)
            return {'type': 'ir.actions.act_window_close'}

    def update_ding_employee(self):
        """
        修改员工时同步至钉钉
        :return:
        """
        self.ensure_one()
        client = dingtalk_api.get_client()
        # 获取部门ding_id
        department_list = list()
        if not self.department_id:
            raise UserError("请选择员工部门!")
        elif self.department_ids:
            department_list = self.department_ids.mapped('ding_id')
            if self.department_id.ding_id not in self.department_ids.mapped('ding_id'):
                department_list.append(self.department_id.ding_id)
        else:
            department_list.append(self.department_id.ding_id)
        data = {
            'userid': self.ding_id,  # userid
            'name': self.name,  # 名称
            'department': department_list,  # 部门
            'position': self.job_title if self.job_title else '',  # 职位
            'mobile': self.mobile_phone if self.mobile_phone else self.work_phone,  # 手机
            'tel': self.work_phone if self.work_phone else '',  # 手机
            'workPlace': self.work_location if self.work_location else '',  # 办公地址
            'remark': self.notes if self.notes else '',  # 备注
            'email': self.work_email if self.work_email else '',  # 邮箱
            'jobnumber': self.din_jobnumber if self.din_jobnumber else '',  # 工号
            'isSenior': self.din_isSenior,  # 高管模式
            'isHide': self.din_isHide,  # 隐藏手机号
        }
        if self.din_hiredDate:
            hiredDate = dingtalk_api.datetime_to_stamp(self.din_hiredDate)
            data.update({'hiredDate': hiredDate})
        try:
            result = client.user.update(data)
            self.message_post(body=u"已成功更新至钉钉", message_type='notification')
            _logger.info(_("已在钉钉上更新Id:{}的员工".format(self.ding_id)))
        except Exception as e:
            raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def delete_ding_employee(self):
        for res in self:
            if not res.ding_id:
                continue
            self._delete_dingtalk_employee_by_id(res.ding_id)
            res.write({'ding_id': False})
            res.message_post(body=u"已在钉钉上删除员工。 *_*!", message_type='notification')
        return {'type': 'ir.actions.act_window_close'}

    def _delete_dingtalk_employee_by_id(self, ding_id):
        client = dingtalk_api.get_client()
        try:
            result = client.user.delete(ding_id)
            _logger.info(_("已在钉钉上删除Id:{}的员工".format(result)))
        except Exception as e:
            raise UserError(e)
        return

    def unlink(self):
        for res in self:
            if res.ding_id and dingtalk_api.get_delete_is_synchronous():
                self._delete_dingtalk_employee_by_id(res.ding_id)
            return super(HrEmployee, self).unlink()

    # TODO 从钉钉手动获取用户详情
    def update_employee_from_dingding(self):
        """
        从钉钉获取用户详情
        :return:
        """
        raise UserError(_("未维护功能！"))
        url = self.env['dingding.parameter'].search([('key', '=', 'user_get')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        for employee in self:
            data = {'userid': employee.ding_id}
            try:
                result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    data = {
                        'name': result.get('name'),  # 员工名称
                        'ding_id': result.get('userid'),  # 钉钉用户Id
                        'din_unionid': result.get('unionid'),  # 钉钉唯一标识
                        'mobile_phone': result.get('mobile'),  # 手机号
                        'work_phone': result.get('tel'),  # 分机号
                        'work_location': result.get('workPlace'),  # 办公地址
                        'notes': result.get('remark'),  # 备注
                        'job_title': result.get('position'),  # 职位
                        'work_email': result.get('email'),  # email
                        'din_jobnumber': result.get('jobnumber'),  # 工号
                        'din_avatar': result.get('avatar') if result.get('avatar') else '',  # 钉钉头像url
                        'din_isSenior': result.get('isSenior'),  # 高管模式
                        'din_isAdmin': result.get('isAdmin'),  # 是管理员
                        'din_isBoss': result.get('isBoss'),  # 是老板
                        'din_isHide': result.get('isHide'),  # 隐藏手机号
                        'din_active': result.get('active'),  # 是否激活
                        'din_isLeaderInDepts': result.get('isLeaderInDepts'),  # 是否为部门主管
                        'din_orderInDepts': result.get('orderInDepts'),  # 所在部门序位
                    }
                    # 支持显示国际手机号
                    if result.get('stateCode') != '86':
                        data.update({
                            'mobile_phone': '+{}-{}'.format(result.get('stateCode'), result.get('mobile')),
                        })
                    if result.get('hiredDate'):
                        date_str = self.timestamp_to_local_date(result.get('hiredDate'))
                        data.update({
                            'din_hiredDate': date_str,
                        })
                    if result.get('department'):
                        dep_ding_ids = result.get('department')
                        dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_ding_ids)])
                        data.update({'department_ids': [(6, 0, dep_list.ids)]})
                    employee.sudo().write(data)
                else:
                    _logger.info("从钉钉同步员工时发生意外，原因为:{}".format(result.get('errmsg')))
                    employee.message_post(body="从钉钉同步员工失败:{}".format(result.get('errmsg')), message_type='notification')

            except ReadTimeout:
                raise UserError("从钉钉同步员工详情超时！")

    def using_dingding_avatar(self):
        """
        单独获取钉钉头像设为员工头像
        :return:
        """
        for emp in self:
            if emp.ding_avatar_url:
                binary_data = base64.b64encode(requests.get(emp.ding_avatar_url).content)
                emp.sudo().write({'image': binary_data})

