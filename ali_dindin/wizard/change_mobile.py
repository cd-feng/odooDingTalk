# -*- coding: utf-8 -*-
import logging
import requests
import json
from requests import ReadTimeout
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChangeMobile(models.TransientModel):
    _name = 'change.mobile'
    _description = 'Change Mobile'

    name = fields.Char('员工姓名', required=True, readonly= True)
    din_id = fields.Char('钉钉ID', required=True, readonly= True)
    dep_din_id = fields.Char('所属部门ID列表', required=True, readonly= True)
    old_mobile = fields.Char('原手机号', readonly= True)
    new_mobile = fields.Char('新手机号', required= True)
    din_active = fields.Boolean('是否激活', required= True)

    def _sanitization(self, record, field_name):
        value = record[field_name]
        if value:
            return value

    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        return records

    @api.model
    def default_get(self, fields):
        result = super(ChangeMobile, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        model = self.env[active_model]
        records = self._get_records(model)
        for record in records:
            result = {
                'name': self._sanitization(record,'name'),
                'din_id': self._sanitization(record,'din_id'),
                'dep_din_id': self._sanitization(record,'department_id').din_id,
                'old_mobile': self._sanitization(record,'mobile_phone'),
                'din_active': self._sanitization(record,'din_active')
            }
        return result

    # 员工钉钉换手机号
    def change_mobile_action(self):
        """强制更换手机号
           -如果手机号未激活，通过更新手机字段实现
           -如果手机号已经激活，则通过先删除该钉钉号，再重新创建钉钉号实现，新建的钉钉号使用老的userid
           -如果该员工有使用钉钉人脸考勤，需要重新录人脸，否则无法继续考勤
           -常见手机号错误代码：
            60103 手机号码不合法,比如说号码位数不正确，国际号码前没有国家代号等等；
            60104 手机号码在公司中已存在；
            40019 该手机号码对应的用户最多可以加入5个非认证企业；
            40021 该手机号码已经注册过钉钉。
        """
        # 先尝试直接更新
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_update')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        headers = {'Content-Type': 'application/json'}
        data = {
            'userid': self.din_id,  # userid
            'name': self.name,  # 姓名
            'department': [self.dep_din_id],
            'mobile': self.new_mobile,  # 手机
        }
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(result)
            if result.get('errcode') == 0:
                employee = self.env['hr.employee'].search([('din_id', '=', self.din_id)])
                if employee:
                    employee.sudo().write({'mobile_phone': self.new_mobile})
            else:
                # 如果手机号已经激活或者新手机号注册过钉钉，先删除钉钉号再新建
                url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_delete')]).value
                token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
                data = {
                    'userid': self.din_id,  # userid
                }
                try:
                    result = requests.get(url="{}{}".format(url, token), params=data, timeout=20)
                    result = json.loads(result.text)
                    logging.info("user_delete:{}".format(result)) 
                    employee = self.env['hr.employee'].search([('din_id', '=', self.din_id)])
                    if employee:
                        if result.get('errcode') == 0:
                            employee.message_post(body="原号码已经在钉钉上删除，等待新建钉钉号", message_type='notification')
                        else:
                            employee.message_post(body="原号码在钉钉已经不存在，等待新建钉钉号", message_type='notification')
                except ReadTimeout:
                    raise UserError("删除钉钉号超时！")

                # 不管是否删除成功，只要保证原号码在钉钉上已经不存在，马上新建钉钉号
                url = self.env['ali.dindin.system.conf'].search([('key', '=', 'user_create')]).value
                token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
                headers = {'Content-Type': 'application/json'}
                data = {
                    'userid': self.din_id,  # userid
                    'name': self.name,  # 姓名
                    'department': [self.dep_din_id],
                    'mobile': self.new_mobile,  # 手机
                }
                try:
                    result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=10)
                    result = json.loads(result.text)
                    logging.info(result)
                    if result.get('errcode') == 0:
                        employee = self.env['hr.employee'].search([('din_id', '=', self.din_id)])
                        if employee:
                            employee.sudo().write({'mobile_phone': self.new_mobile})
                            employee.update_ding_employee() # 换号码后把员工其他信息同步到钉钉
                            employee.update_employee_from_dingding() # 换号码后从钉钉获取新手机的激活状态
                            employee.message_post(body="通过删除后重建更换手机号为:{}".format(self.new_mobile), message_type='notification')
                    else:
                        raise UserError('上传钉钉系统时发生错误，详情为:{}'.format(result.get('errmsg')))
                except ReadTimeout:
                    raise UserError("删除钉钉号超时！")
        except ReadTimeout:
            raise UserError("删除钉钉号超时！")