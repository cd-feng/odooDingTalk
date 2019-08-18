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
import time
from requests import ReadTimeout
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ding_id = fields.Char(string='钉钉用户Id', index=True)
    din_unionid = fields.Char(string='钉钉唯一标识', index=True)
    din_jobnumber = fields.Char(string='钉钉员工工号')
    din_avatar = fields.Char(string='钉钉头像url')
    din_hiredDate = fields.Datetime(string='入职时间')
    din_isAdmin = fields.Boolean("是管理员", default=False)
    din_isBoss = fields.Boolean("是老板", default=False)
    din_isLeader = fields.Boolean("是部门主管", default=False)
    din_isHide = fields.Boolean("隐藏手机号", default=False)
    din_isSenior = fields.Boolean("高管模式", default=False)
    din_active = fields.Boolean("是否激活", readonly=True)
    din_orderInDepts = fields.Char("所在部门序位")
    din_isLeaderInDepts = fields.Char("是否为部门主管")
    din_sy_state = fields.Boolean(string=u'同步标识', default=False)
    work_status = fields.Selection(string=u'入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')], default='2')
    office_status = fields.Selection(string=u'在职子状态', selection=[('2', '试用期'), ('3', '正式'), ('5', '待离职'), ('-1', '无状态')], default='-1')
    dingding_type = fields.Selection(string=u'钉钉状态', selection=[('no', '不存在'), ('yes', '存在')], compute="_compute_dingding_type")
    department_ids = fields.Many2many('hr.department', 'employee_department_rel', 'emp_id', 'department_id', string='所属部门')

    # 上传员工到钉钉
    @api.multi
    def create_ding_employee(self):
        """
        上传员工到钉钉
        :return:
        """
        for res in self:
            url = self.env['dingding.parameter'].search([('key', '=', 'user_create')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
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
                'mobile': res.mobile_phone if res.mobile_phone else '',  # 手机
                'tel': res.work_phone if res.work_phone else '',  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=10)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    res.write({'ding_id': result.get('userid')})
                    res.message_post(body=u"钉钉消息：员工信息已上传至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传员工至钉钉超时！")

    # 修改员工同步到钉钉
    @api.multi
    def update_ding_employee(self):
        """
        修改员工时同步至钉钉
        :return:
        """
        for res in self:
            url = self.env['dingding.parameter'].search([('key', '=', 'user_update')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            # 获取部门ding_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            elif res.department_ids:
                department_list = res.department_ids.mapped('ding_id')
                if not res.department_id.ding_id in res.department_ids.mapped('ding_id'):
                    department_list.append(res.department_id.ding_id)
            else:
                department_list.append(res.department_id.ding_id)
            _logger.info(department_list)
            data = {
                'userid': res.ding_id,  # userid
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else '',  # 手机
                'tel': res.work_phone if res.work_phone else '',  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
                'isSenior': res.din_isSenior,  # 高管模式
                'isHide': res.din_isHide,  # 隐藏手机号
            }
            if res.din_hiredDate:
                hiredDate = self.date_to_stamp(res.din_hiredDate)
                data.update({'hiredDate': hiredDate})

            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data),
                                       timeout=30)
                result = json.loads(result.text)
                logging.info(result)
                if result.get('errcode') == 0:
                    res.message_post(body=u"新的信息已同步更新至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传员工至钉钉超时！")

    @api.constrains('user_id')
    def constrains_dingding_user_id(self):
        """
        当选择了相关用户时，需要检查系统用户是否只对应一个员工
        :return:
        """
        if self.user_id:
            emps = self.sudo().search([('user_id', '=', self.user_id.id)])
            if len(emps) > 1:
                raise UserError("Sorry!，关联的相关(系统)用户已关联到其他员工，若需要变更请修改原关联的相关用户！")
            # 把员工的钉钉id和手机号写入到系统用户oauth
            if self.ding_id and self.mobile_phone:
                self._cr.execute("""UPDATE res_users SET ding_user_id='{}',ding_user_phone='{}' WHERE id={}""".format(self.ding_id, self.mobile_phone, self.user_id.id))

    # 从钉钉手动获取用户详情
    @api.multi
    def update_employee_from_dingding(self):
        """
        从钉钉获取用户详情
        :return:
        """
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
                            'mobile_phone':'+{}-{}'.format(result.get('stateCode'), result.get('mobile')),
                        })
                    if result.get('hiredDate'):
                        date_str = self.get_time_stamp(result.get('hiredDate'))
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

    # 重写删除方法
    @api.multi
    def unlink(self):
        for res in self:
            userid = res.ding_id
            super(HrEmployee, self).unlink()
            din_delete_employee = self.env['ir.config_parameter'].sudo().get_param('dingding_base.din_delete_employee')
            if din_delete_employee:
                self.delete_din_employee(userid)
            return True

    @api.model
    def delete_din_employee(self, userid):
        """
        删除钉钉用户
        :param userid:
        :return:
        """
        url = self.env['dingding.parameter'].search([('key', '=', 'user_delete')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        data = {
            'userid': userid,  # userid
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
            result = json.loads(result.text)
            logging.info("user_delete:{}".format(result))
            if result.get('errcode') != 0:
                raise UserError('删除钉钉用户时发生错误，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("上传员工至钉钉超时！")

    def _compute_dingding_type(self):
        for res in self:
            res.dingding_type = 'yes' if res.ding_id else 'no'

    # 单独获取钉钉头像设为员工头像
    @api.multi
    def using_dingding_avatar(self):
        """
        单独获取钉钉头像设为员工头像
        :return:
        """
        for emp in self:
            if emp.din_avatar:
                binary_data = tools.image_resize_image_big(base64.b64encode(requests.get(emp.din_avatar).content))
                emp.sudo().write({'image': binary_data})

    @api.model
    def get_time_stamp(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000) 
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    # 把时间转成时间戳形式
    @api.model
    def date_to_stamp(self, date):
        """
        将时间转成13位时间戳
        :param time_num:
        :return:
        """
        date_str = fields.Datetime.to_string(date)
        date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
        date_stamp = date_stamp * 1000
        return date_stamp

