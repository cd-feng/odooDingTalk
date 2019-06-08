# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


# 拓展部门员工
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    din_id = fields.Char(string='钉钉用户Id')
    din_unionid = fields.Char(string='钉钉唯一标识')
    din_jobnumber = fields.Char(string='钉钉员工工号')
    din_avatar = fields.Char(string='钉钉头像url')
    din_hiredDate = fields.Date(string='入职时间')
    din_sy_state = fields.Boolean(string=u'同步标识', default=False)
    work_status = fields.Selection(string=u'工作状态', selection=[(1, '待入职'), (2, '试用期'), (3, '正式员工'), (4, '离职')])
    dingding_type = fields.Selection(string=u'钉钉状态', selection=[('no', '不存在'), ('yes', '存在')], compute="_compute_dingding_type")


    # 上传员工到钉钉
    @api.multi
    def create_ding_employee(self):
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_create')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            # 获取部门din_id
            department_list = list()
            if res.department_id:
                department_list.append(res.department_id.din_id)
            else:
                raise UserError("请选择员工部门!")
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
                    res.write({'din_id': result.get('userid')})
                    res.message_post(body=u"钉钉消息：员工信息已上传至钉钉", message_type='notification')
                else:
                    raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("上传员工至钉钉超时！")

    # 修改员工同步到钉钉
    @api.multi
    def update_ding_employee(self):
        """修改员工时同步至钉钉"""
        for res in self:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            # 获取部门din_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            data = {
                'userid': res.din_id,  # userid
                'name': res.name,  # 名称
                'department': department_list.append(res.department_id.din_id),  # 部门
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
        """当选择了相关用户时，需要检查系统用户是否只对应一个员工"""
        if self.user_id:
            emps = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id)])
            if len(emps) > 1:
                raise UserError("Sorry!，关联的相关(系统)用户已关联到其他员工，若需要变更请修改原关联的相关用户！")

    # 重写删除方法
    @api.multi
    def unlink(self):
        for res in self:
            userid = res.din_id
            super(HrEmployee, self).unlink()
            din_delete_employee = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_employee')
            if din_delete_employee:
                self.delete_din_employee(userid)
            return True

    @api.model
    def delete_din_employee(self, userid):
        """删除钉钉用户"""
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_delete')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
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
            res.dingding_type = 'yes' if res.din_id else 'no'

    # 单独获取钉钉头像设为员工头像
    @api.multi
    def using_dingding_avatar(self):
        for emp in self:
            if emp.din_avatar:
                binary_data = tools.image_resize_image_big(base64.b64encode(requests.get(emp.din_avatar).content))
                emp.sudo().write({'image': binary_data})

# 未使用，但是不能删除，因为第一个版本创建的视图还存在
class DinDinSynchronousEmployee(models.TransientModel):
    _name = 'dindin.synchronous.employee'
    _description = "同步钉钉部门员工功能模型"
