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
import logging
import time

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REASONTYPE = [
    ('1', '家庭原因'),
    ('2', '个人原因'),
    ('3', '发展原因'),
    ('4', '合同到期不续签'),
    ('5', '协议解除'),
    ('6', '无法胜任工作'),
    ('7', '经济性裁员'),
    ('8', '严重违法违纪'),
    ('9', '其他'),
]
PRESTATUS = [
    ('1', '待入职'),
    ('2', '试用期'),
    ('3', '正式'),
    ('4', '未知'),
    ('5', '未知'),
]


class EmployeeRoster(models.Model):
    _name = 'dingding.employee.roster'
    _description = "员工花名册"

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id, index=True)

    # 钉钉提供的标准字段
    name = fields.Char(string='姓名')
    ding_userid = fields.Char(string='钉钉用户Id', index=True)
    email = fields.Char(string='邮箱')
    dept = fields.Many2many('hr.department', string=u'部门', help="适应钉钉多部门")
    mainDept = fields.Many2one('hr.department', string=u'主部门', index=True)
    position = fields.Many2one(comodel_name='hr.job', string=u'职位')
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

    # 离职员工相关字段
    last_work_day = fields.Datetime(string='最后工作时间')
    reason_memo = fields.Text(string="离职原因")
    reason_type = fields.Selection(string='离职类型', selection=REASONTYPE)
    pre_status = fields.Selection(string='离职前工作状态', selection=PRESTATUS)
    handover_userid = fields.Many2one(
        comodel_name='dingding.employee.roster', string='离职交接人')

    @api.constrains('certNo')
    def _constrains_employee_identification_id(self):
        """
        将花名册里面部分信息改写到员工信息中
        :return:
        """
        for res in self:
            res.emp_id.sudo().write({
                'identification_id': res.certNo,
            })


class EmployeeRosterSynchronous(models.TransientModel):
    _name = 'dingding.employee.roster.synchronous'
    _description = "智能人事花名册同步"

    @api.model
    def get_onjob_userid_list(self):
        """
        获取在职员工userid列表
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        onjob_list = list()
        status_arr = ['2', '3', '5', '-1']
        offset = 0
        size = 50
        while True:
            try:
                result = din_client.employeerm.queryonjob(status_list=status_arr, offset=offset, size=size)
                # logging.info(">>>获取在职员工列表返回结果%s", result)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                        onjob_list.extend(result_list)
                    else:
                        break
                else:
                    break
            except Exception as e:
                raise UserError(e)
        return onjob_list

    @api.multi
    def get_onjob_list(self):
        """
        获取钉钉在职员工花名册
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉在职员工花名册start")
        emp_data = self.get_employee_to_dict()
        onjob_userid_list = self.get_onjob_userid_list()
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(onjob_userid_list, 20)
        for u in user_list:
            try:
                result = din_client.employeerm.list(u, field_filter_list=())
                if result.get('emp_field_info_v_o'):
                    for rec in result.get('emp_field_info_v_o'):
                        roster_data = {
                            'emp_id': emp_data[rec['userid']] if rec['userid'] in emp_data else False,
                            'ding_userid': rec['userid']
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            # 获取部门（可能会多个）
                            if fie['field_code'][6:] == 'deptIds' and 'value' in fie:
                                dept_ding_ids = list()
                                for depa in fie['value'].split('|'):
                                    dept_ding_ids.append(depa)
                                departments = self.env['hr.department'].sudo().search(
                                    [('ding_id', 'in', dept_ding_ids)])
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId' and 'value' in fie:
                                dept = self.env['hr.department'].sudo().search(
                                    [('ding_id', '=', fie['value'])], limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position' and 'label' in fie:
                                hr_job = self.env['hr.job'].sudo().search([('name', '=', fie['label'])])
                                if not hr_job and fie['label']:
                                    hr_job = self.env['hr.job'].sudo().create({'name': fie['label']})
                                roster_data.update({
                                    'position': hr_job.id
                                })
                            # 同步姓名
                            elif fie['field_code'][6:] == 'name' and 'value' in fie:
                                roster_data.update({'name': fie['value']})
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else ''
                                })
                        roster = self.env['dingding.employee.roster'].sudo().search(
                            [('ding_userid', '=', rec['userid'])])
                        if roster:
                            roster.sudo().write(roster_data)
                        else:
                            self.env['dingding.employee.roster'].sudo().create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        logging.info(">>>获取钉钉在职员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_employee_roster_action')
        action_dict = action.read()[0]
        return action_dict

    @api.multi
    def dimission_list_synchronous(self):
        self.ensure_one()
        # 获取离职花名册
        self.get_dimission_list()
        # 更新离职信息
        self.get_dimission_info()

    @api.model
    def get_dimission_userid_list(self):
        """
        获取离职员工userid列表
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        dimission_list = list()
        offset = 0
        size = 50
        while True:
            try:
                result = din_client.employeerm.querydimission(offset=offset, size=size)
                # logging.info(">>>获取离职员工列表返回结果%s", result)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                        dimission_list.extend(result_list)
                    else:
                        break
                else:
                    break
            except Exception as e:
                raise UserError(e)
        return dimission_list

    @api.multi
    def get_dimission_list(self):
        """
        获取钉钉离职员工花名册
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉离职员工花名册start")
        emp_data = self.get_employee_to_dict()
        dimission_userid_list = self.get_dimission_userid_list()
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(dimission_userid_list, 20)
        for u in user_list:
            try:
                result = din_client.employeerm.list(u, field_filter_list=())
                # logging.info(">>>获取花名册返回结果%s", result)
                if result.get('emp_field_info_v_o'):
                    for rec in result.get('emp_field_info_v_o'):
                        # logging.info(">>>当前离职员工%s", rec)
                        roster_data = {
                            'emp_id': emp_data[rec['userid']] if rec['userid'] in emp_data else False,
                            'ding_userid': rec['userid']
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            # 获取部门（可能会多个）
                            if fie['field_code'][6:] == 'deptIds' and 'value' in fie:
                                dept_ding_ids = list()
                                for depa in fie['value'].split('|'):
                                    dept_ding_ids.append(depa)
                                departments = self.env['hr.department'].sudo().search(
                                    [('ding_id', 'in', dept_ding_ids)])
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId' and 'value' in fie:
                                dept = self.env['hr.department'].sudo().search(
                                    [('ding_id', '=', fie['value'])], limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position' and 'label' in fie:
                                if fie['label']:
                                    hr_job = self.env['hr.job'].sudo().search([('name', '=', fie['label'])])
                                    if not hr_job and fie['label']:
                                        hr_job = self.env['hr.job'].sudo().create({'name': fie['label']})
                                roster_data.update({
                                    'position': hr_job.id
                                })
                            # 同步姓名
                            elif fie['field_code'][6:] == 'name' and 'value' in fie:
                                roster_data.update({'name': fie['value']})
                            else:
                                roster_data.update({
                                    fie['field_code'][6:]: fie['label'] if "label" in fie else ''
                                })
                        roster = self.env['dingding.employee.roster'].sudo().search(
                            [('ding_userid', '=', rec['userid'])])
                        if roster:
                            roster.sudo().write(roster_data)
                        else:
                            self.env['dingding.employee.roster'].sudo().create(roster_data)
                else:
                    raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        logging.info(">>>获取钉钉离职员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_employee_roster_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def get_dimission_info(self):
        """
        批量获取员工离职信息
        根据传入的staffId列表，批量查询员工的离职信息
        :param userid_list: 员工id
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉离职员工信息start")
        # emp_data = self.get_employee_to_dict()
        dimission_userid_list = self.get_dimission_userid_list()
        user_list = self.env['hr.attendance.tran'].sudo().list_cut(dimission_userid_list, 50)
        for u in user_list:
            try:
                result = din_client.employeerm.listdimission(userid_list=u)
                # logging.info(">>>批量获取员工离职信息返回结果%s", result)
                if result.get('emp_dimission_info_vo'):
                    for res in result.get('emp_dimission_info_vo'):
                        data = {
                            'last_work_day': self.stamp_to_time(res.get('last_work_day')),
                            'reason_memo': res.get('reason_memo'),
                            'reason_type': str(res.get('reason_type')) if res.get('reason_type') else '9',
                            'pre_status': str(res.get('pre_status'))
                        }
                        if res.get('handover_userid'):
                            handover_userid = self.env['dingding.employee.roster'].search(
                                [('ding_userid', '=', res.get('handover_userid'))])
                            data.update({'handover_userid': handover_userid.id})
                        emp = self.env['dingding.employee.roster'].search(
                            [('ding_userid', '=', res.get('userid'))])
                        if emp:
                            emp.write(data)
                        # else:
                        #     self.env['dingding.hrm.dimission.list'].create(data)

            except Exception as e:
                raise UserError(e)
        logging.info(">>>获取获取离职员工信息end")

    def get_employee_to_dict(self):
        """
        将员工封装为字典并返回
        :return:
        """
        employees = self.env['hr.employee'].sudo().search([('ding_id', '!=', '')])
        emp_data = dict()
        for emp in employees:
            emp_data.update({
                emp.ding_id: emp.id,
            })
        return emp_data

    def stamp_to_time(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000)
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
