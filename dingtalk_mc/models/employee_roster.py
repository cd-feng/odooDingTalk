# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EmployeeRoster(models.Model):
    _name = 'dingtalk.employee.roster'
    _description = "员工花名册"

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
    EMPLOYEESTATE = [
        ('无状态', '无状态'),
        ('试用', '试用'),
        ('正式', '正式'),
        ('待离职', '待离职'),
        ('离职', '离职'),
        ('未知', '未知'),
    ]
    EMPLOYEETYPES = [
        ('无类型', '无类型'),
        ('全职', '全职'),
        ('兼职', '兼职'),
        ('实习', '实习'),
        ('劳务派遣', '劳务派遣'),
        ('退休返聘', '退休返聘'),
        ('劳务外包', '劳务外包'),
    ]

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', index=True)
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.company, index=True)
    active = fields.Boolean('Active', default=True, store=True, readonly=False)
    color = fields.Integer(string=u'颜色标签')
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
    employeeType = fields.Selection(string=u'员工类型', selection=EMPLOYEETYPES)
    employeeStatus = fields.Selection(string=u'员工状态', selection=EMPLOYEESTATE)
    probationPeriodType = fields.Char(string='试用期')
    regularTime = fields.Char(string='转正日期')
    positionLevel = fields.Char(string='岗位职级')
    realName = fields.Char(string='身份证姓名')
    certNo = fields.Char(string='证件号码')
    birthTime = fields.Char(string='出生日期')
    sexType = fields.Selection(string=u'性别', selection=[('男', '男'), ('女', '女')])

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
    handover_userid = fields.Many2one(comodel_name='dingtalk.employee.roster', string='离职交接人')

    def name_get(self):
        """
        重写name_get方法
        :return:
        """
        return [(res.id, '%s-%s' % (res.mainDept.name, res.name)) for res in self]

