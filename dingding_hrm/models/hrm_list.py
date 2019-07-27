# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingHrmList(models.Model):
    _name = 'dingding.hrm.list'
    _description = "获取员工花名册"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门')
    line_ids = fields.One2many(comodel_name='dingding.hrm.list.line', inverse_name='list_is', string=u'信息列表')
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)


class DingDingHrmListline(models.Model):
    _name = 'dingding.hrm.list.line'
    _description = "获取员工花名册明细"
    _rec_name = 'list_is'

    list_is = fields.Many2one(comodel_name='dingding.hrm.list', string=u'获取员工花名册', ondelete='cascade')
    sequence = fields.Integer(string=u'序号')
    group_id = fields.Char(string='字段分组ID')
    value = fields.Char(string='值')
    label = fields.Char(string='参照值')
    field_code = fields.Char(string='字段编码')
    field_name = fields.Char(string='字段名')


class GetDingDingHrmList(models.TransientModel):
    _name = 'dingding.get.hrm.list'
    _description = '获取钉钉员工花名册'

    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_hrm_list_and_hr_employee_rel',
                               column1='list_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_hrm_list(self):
        """
        获取钉钉员工花名册
        :return:
        """
        logging.info(">>>获取钉钉员工花名册start")
        if len(self.emp_ids) > 20:
            raise UserError("钉钉仅支持批量查询小于等于20个员工!")
        url = self.env['dingding.parameter'].search([('key', '=', 'hrm_list')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        user_str = ''
        for user in self.emp_ids:
            if user_str == '':
                user_str = user_str + "{}".format(user.ding_id)
            else:
                user_str = user_str + ",{}".format(user.ding_id)
        data = {'userid_list': user_str}
        try:
            headers = {'Content-Type': 'application/json'}
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                for res in result.get('result'):
                    line_list = list()
                    for field_list in res.get('field_list'):
                        line_list.append((0, 0, {
                            'group_id': field_list.get('group_id'),
                            'value': field_list.get('value'),
                            'label': field_list.get('label'),
                            'field_code': field_list.get('field_code'),
                            'field_name': field_list.get('field_name'),
                        }))
                    emp = self.env['hr.employee'].search([('ding_id', '=', res.get('userid'))])
                    if emp:
                        hrm = self.env['dingding.hrm.list'].search([('emp_id', '=', emp[0].id)])
                        if hrm:
                            hrm.write({
                                'department_id': emp[0].department_id.id,
                                'line_ids': line_list
                            })
                        else:
                            self.env['dingding.hrm.list'].sudo().create({
                                'emp_id': emp[0].id,
                                'department_id': emp[0].department_id.id,
                                'line_ids': line_list
                            })
            else:
                raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时")
        logging.info(">>>获取钉钉员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_hrm_list_action')
        action_dict = action.read()[0]
        return action_dict
