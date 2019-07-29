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


class EmployeeRoster(models.Model):
    _name = 'dingding.employee.roster'
    _description = "员工花名册"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id, index=True)

    # 钉钉提供的标准字段
    name = fields.Char(string='姓名')
    ding_userid = fields.Char(string='钉钉用户Id', index=True)
    email = fields.Char(string='邮箱')
    dept = fields.Many2one('hr.department', string=u'部门', index=True)
    mainDept = fields.Many2one('hr.department', string=u'主部门', index=True)
    position = fields.Char(string='职位')
    mobile = fields.Char(string='手机号')
    jobNumber = fields.Char(string='工号')
    tel = fields.Char(string='分机号')
    workPlace = fields.Char(string='办公地点')
    remark = fields.Char(string='备注')
    confirmJoinTime = fields.Char(string='入职时间')
    employeeType = fields.Char(string='员工类型')
    employeeStatus = fields.Char(string='员工状态')
    probationPeriodType = fields.Char(string='试用期')
    regularTime = fields.Char(string='转正日期')
    positionLevel = fields.Char(string='岗位职级')
    realName = fields.Char(string='身份证姓名')
    certNo = fields.Char(string='证件号码')
    birthTime = fields.Char(string='出生日期')
    sexType = fields.Char(string='性别')
    nationType = fields.Char(string='民族')
    certAddress = fields.Char(string='身份证地址')
    certEndTime = fields.Char(string='证件有效期')
    marriage = fields.Char(string='婚姻状况')
    joinWorkingTime = fields.Char(string='首次参加工作时间')
    residenceType = fields.Char(string='户籍类型')
    address = fields.Char(string='住址')
    politicalStatus = fields.Char(string='政治面貌')
    personalSi = fields.Char(string='个人社保账号')
    personalHf = fields.Char(string='个人公积金账号')
    highestEdu = fields.Char(string='最高学历')
    graduateSchool = fields.Char(string='毕业院校')
    graduationTime = fields.Char(string='毕业时间')
    major = fields.Char(string='所学专业')
    bankAccountNo = fields.Char(string='银行卡号')
    accountBank = fields.Char(string='开户行')
    contractCompanyName = fields.Char(string='合同公司')
    contractType = fields.Char(string='合同类型')
    firstContractStartTime = fields.Char(string='首次合同起始日')
    firstContractEndTime = fields.Char(string='首次合同到期日')
    nowContractStartTime = fields.Char(string='现合同起始日')
    nowContractEndTime = fields.Char(string='现合同到期日')
    contractPeriodType = fields.Char(string='合同期限')
    contractRenewCount = fields.Char(string='续签次数')
    urgentContactsName = fields.Char(string='紧急联系人姓名')
    urgentContactsRelation = fields.Char(string='联系人关系')
    urgentContactsPhone = fields.Char(string='联系人电话')
    haveChild = fields.Char(string='有无子女')
    childName = fields.Char(string='子女姓名')
    childSex = fields.Char(string='子女性别')
    childBirthDate = fields.Char(string='子女出生日期')


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
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('hrm_list')
        emp_data, dept_data = self.get_employee_to_dict()
        user_list = list()
        for emp in self.emp_ids:
            if emp.ding_id:
                user_list.append(emp.ding_id)
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(user_list, 20)
        for u in user_list:
            user_str = ",".join(u)
            data = {'userid_list': user_str}
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    for rec in result['result']:
                        roster_data = {
                            'emp_id': emp_data[rec['userid']] if rec['userid'] in emp_data else False,
                            'ding_userid': rec['userid']
                        }
                        for fie in rec['field_list']:
                            # 判断部门和主部门
                            if fie['field_code'][6:] == 'deptIds':
                                roster_data.update({
                                    'dept': dept_data[str(fie['label'])],
                                    'mainDept': dept_data[str(fie['label'])]
                                })
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept' or fie['field_code'][6:] == 'deptIds':
                                continue
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else ''
                                })
                        roster = self.env['dingding.employee.roster'].sudo().search([('ding_userid', '=', rec['userid'])])
                        if roster:
                            roster.sudo().write(roster_data)
                        else:
                            self.env['dingding.employee.roster'].sudo().create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        logging.info(">>>获取钉钉员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_employee_roster_action')
        action_dict = action.read()[0]
        return action_dict

    def get_employee_to_dict(self):
        """
        将员工、部门封装为字典并返回
        :return:
        """
        employees = self.env['hr.employee'].sudo().search([('ding_id', '!=', '')])
        departments = self.env['hr.department'].sudo().search([('ding_id', '!=', '')])
        emp_data = dict()
        for emp in employees:
            emp_data.update({
                emp.ding_id: emp.id,
            })
        dept_data = dict()
        for dept in departments:
            dept_data.update({
                dept.ding_id: dept.id,
            })
        return emp_data, dept_data
