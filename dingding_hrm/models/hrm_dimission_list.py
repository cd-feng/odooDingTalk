# -*- coding: utf-8 -*-
import json
import logging
import time

import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingHrmDimissionList(models.Model):
    _name = 'dingding.hrm.dimission.list'
    _description = "离职员工信息"
    _rec_name = 'emp_id'

    REASONTYPE = [
        (1, '家庭原因'),
        (2, '个人原因'),
        (3, '发展原因'),
        (4, '合同到期不续签'),
        (5, '协议解除'),
        (6, '无法胜任工作'),
        (7, '经济性裁员'),
        (8, '严重违法违纪'),
        (9, '其他'),
    ]
    PRESTATUS = [
        (1, '待入职'),
        (2, '试用期'),
        (3, '正式'),
    ]
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    last_work_day = fields.Datetime(string=u'最后工作时间')
    department_id = fields.Many2many(comodel_name='hr.department', relation='hrm_dimission_and_depatment_rel',
                                     column1='list_id', column2='dept_id', string=u'部门')
    reason_memo = fields.Text(string=u"离职原因")
    reason_type = fields.Selection(string=u'离职类型', selection=REASONTYPE)
    pre_status = fields.Selection(string=u'离职前工作状态', selection=PRESTATUS)
    handover_userid = fields.Many2one(comodel_name='hr.employee', string=u'离职交接人')
    status = fields.Selection(string=u'离职状态', selection=[(1, '待离职'), (2, '已离职')])
    main_dept_name = fields.Many2one(comodel_name='hr.department', string=u'离职前主部门')
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)


class GetDingDingHrmDimissionList(models.TransientModel):
    _name = 'dingding.get.hrm.dimission.list'
    _description = '获取离职员工信息'

    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_hrm_dimission_list_and_hr_employee_rel',
                               column1='list_id', column2='emp_id', string=u'员工', required=True)

    @api.multi
    def get_hrm_dimission_list(self):
        """
        获取离职员工信息
        :return:
        """
        logging.info(">>>获取钉钉获取离职员工信息start")
        if len(self.emp_ids) > 50:
            raise UserError("钉钉仅支持批量查询小于等于50个员工!")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'hrm_listdimission')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        user_str = ''
        for user in self.emp_ids:
            if user_str == '':
                user_str = user_str + "{}".format(user.din_id)
            else:
                user_str = user_str + ",{}".format(user.din_id)
        data = {'userid_list': user_str}
        try:
            headers = {'Content-Type': 'application/json'}
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                if len(result.get('result')) < 1:
                    raise UserError("选择的员工未离职!")
                for res in result.get('result'):
                    logging.debug(res)
                    emp = self.env['hr.employee'].search([('din_id', '=', res.get('userid'))])
                    if emp:
                        hrm = self.env['dingding.hrm.dimission.list'].search([('emp_id', '=', emp[0].id)])
                        handover_userid = self.env['hr.employee'].search([('din_id', '=', res.get('handover_userid'))])
                        main_dept = self.env['hr.department'].search([('din_id', '=', res.get('main_dept_id'))])
                        dept_list = list()
                        for depti in res.get('dept_list'):
                            hr_dept = self.env['hr.department'].search([('din_id', '=', depti.get('dept_id'))])
                            if hr_dept:
                                dept_list.append(hr_dept.id)
                        data = {
                            'emp_id': emp[0].id,
                            'last_work_day': self.get_time_stamp(res.get('last_work_day')),
                            'department_id': [(6, 0, dept_list)],
                            'reason_memo': res.get('reason_memo'),
                            'reason_type': res.get('reason_type'),
                            'pre_status': res.get('pre_status'),
                            'handover_userid': handover_userid.id if handover_userid else False,
                            'status': res.get('status'),
                            'main_dept_name': main_dept.id if main_dept else False,
                        }
                        if hrm:
                            hrm.write(data)
                        else:
                            self.env['dingding.hrm.dimission.list'].create(data)
            else:
                raise UserError("获取失败,原因:{}\r\n或许您没有开通智能人事功能，请登录钉钉安装智能人事应用!".format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时")
        logging.info(">>>获取获取离职员工信息end")
        action = self.env.ref('dingding_hrm.dingding_hrm_dimission_list_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间
        :param timeNum:
        :return:
        """
        timeStamp = float(timeNum / 1000)
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime