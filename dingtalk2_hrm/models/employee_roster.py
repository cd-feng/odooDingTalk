# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)

REASON_TYPE = [
    ('1', '家庭原因'), ('2', '个人原因'), ('3', '发展原因'), ('4', '合同到期不续签'), ('5', '协议解除'),
    ('6', '无法胜任工作'), ('7', '经济性裁员'), ('8', '严重违法违纪'), ('9', '其他'),
]
PRE_STATUS = [
    ('1', '待入职'), ('2', '试用期'), ('3', '正式'),
    ('4', '未知'), ('5', '未知'),
]
EMPLOYEE_STATE = [
    ('无状态', '无状态'), ('试用', '试用'), ('正式', '正式'),
    ('待离职', '待离职'), ('离职', '离职'), ('未知', '未知'), ('待入职', '待入职'),
]
EMPLOYEE_TYPES = [
    ('无类型', '无类型'), ('全职', '全职'), ('兼职', '兼职'), ('实习', '实习'),
    ('劳务派遣', '劳务派遣'), ('退休返聘', '退休返聘'), ('劳务外包', '劳务外包'),
]


class EmployeeRoster(models.Model):
    _name = 'dingtalk.employee.roster'
    _description = "员工花名册"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company, index=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='系统员工', index=True, ondelete='cascade')
    image_1920 = fields.Image("Image 1920", related="employee_id.image_1920", store=True)
    # 钉钉提供的标准字段
    name = fields.Char(string='姓名', tracking=True)
    ding_userid = fields.Char(string='钉钉用户Id', index=True)
    email = fields.Char(string='邮箱')
    dept = fields.Many2many('hr.department', string='部门', help="适应钉钉多部门")
    mainDept = fields.Many2one('hr.department', string='主部门', index=True)
    position = fields.Many2one(comodel_name='hr.job', string='职位')
    mobile = fields.Char(string='手机号', tracking=True)
    jobNumber = fields.Char(string='工号', tracking=True)
    tel = fields.Char(string='分机号')
    workPlace = fields.Char(string='办公地点')
    remark = fields.Char(string='备注')
    confirmJoinTime = fields.Char(string='入职时间', tracking=True)
    employeeType = fields.Selection(string='员工类型', selection=EMPLOYEE_TYPES, tracking=True)
    employeeStatus = fields.Selection(string='员工状态', selection=EMPLOYEE_STATE, tracking=True)
    probationPeriodType = fields.Char(string='试用期')
    planRegularTime = fields.Char(string='计划转正日期', tracking=True)
    regularTime = fields.Char(string='实际转正日期', tracking=True)
    positionLevel = fields.Char(string='岗位职级')
    realName = fields.Char(string='身份证姓名')
    certNo = fields.Char(string='证件号码', tracking=True)
    birthTime = fields.Char(string='出生日期')
    sexType = fields.Selection(string='性别', selection=[('男', '男'), ('女', '女')])

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
    contractCompanyName = fields.Char(string='合同公司', tracking=True)
    salaryCompanyName = fields.Char(string='发薪公司', tracking=True)
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
    pre_status = fields.Selection(string='离职前工作状态', selection=PRE_STATUS)
    last_work_day = fields.Date(string="最后工作日", tracking=True)
    reason_memo = fields.Text(string="离职原因")
    reason_type = fields.Selection(string="离职原因类型", selection=REASON_TYPE)
    handover_userid = fields.Many2one(comodel_name="hr.employee", string="离职交接人")
    status = fields.Selection(string="离职状态", selection=[
        ('1', '待离职'), ('2', '已离职'), ('3', '未离职'),
        ('4', '发起离职审批但还未通过'), ('5', '失效')], tracking=True)
    main_dept_name = fields.Char(string="前主部门名称")
    main_dept_id = fields.Char(string="离职前主部门ID")

    @api.constrains('name', 'ding_userid')
    def _constrains_employee(self):
        """
        检查是否存在系统员工
        :return:
        """
        employee_model = self.env['hr.employee'].sudo()
        for res in self:
            if res.ding_userid:
                domain = [('company_id', '=', res.company_id.id), ('ding_id', '=', res.ding_userid)]
                employee_id = employee_model.search(domain, limit=1)
                if employee_id:
                    res.employee_id = employee_id.id
                    # 将花名册中的数据写入到员工中
                    value = {
                        'identification_id': res.certNo,   # 证件号码
                        'work_email': res.email,           # 邮箱
                    }
                    if res.sexType == '男':
                        value['gender'] = 'male'
                    elif res.sexType == '女':
                        value['gender'] = 'female'
                    employee_id.write(value)
