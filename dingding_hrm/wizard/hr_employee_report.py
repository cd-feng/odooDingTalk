# -*- coding:utf-8 -*-
from odoo import fields, models, tools, api
import json
import logging
import requests
from requests import ReadTimeout
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployeeReport(models.Model):
    _name = 'hr_employee_dingding_report'
    _auto = False
    _description = u"员工入职状态"

    id = fields.Integer(string=u'序号')
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门')
    work_status = fields.Selection(string=u'入职状态', selection=[(1, '待入职'), (2, '在职'), (3, '离职')])

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_employee_dingding_report')
        self._cr.execute("""
            CREATE VIEW hr_employee_dingding_report AS (
                SELECT 
                    emp.id as id,
                    emp.company_id as company_id,
                    emp.id as employee_id,
                    emp.department_id as department_id,
                    emp.work_status as work_status
                FROM 
                    hr_employee emp 
        )""")


class GetHrEmployeeStauts(models.TransientModel):
    _name = 'get.hrm.employee.state'
    _description = '查询员工入职状态'

    @api.multi
    def get_hrm_employee_state(self):
        self.ensure_one()
        # 更新待入职员工
        self.get_query_preentry()
        # 更新在职员工
        self.get_queryonjob()
        # 更新离职员工
        self.get_querydimission()

    @api.model
    def get_query_preentry(self):
        """
        更新待入职员工
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'hrm_querypreentry')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        offset = 0
        size = 50
        while True:
            data = {'offset': offset, 'size': size}
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
                result = json.loads(result.text)
                logging.info("待入职员工:{}".format(result))
                if result.get('errcode') == 0:
                    d_res = result['result']
                    for data_list in d_res['data_list']:
                        sql = """UPDATE hr_employee SET work_status=1 WHERE din_id='{}'""".format(data_list)
                        self._cr.execute(sql)
                    if 'next_cursor' in d_res:
                        offset = d_res['next_cursor']
                    else:
                        break
                else:
                    raise UserError("更新失败,原因:{}\r".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        return True

    @api.model
    def get_queryonjob(self):
        """
        更新在职员工,在职员工子状态筛选: 2，试用期；3，正式；5，待离职；-1，无状态
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'hrm_queryonjob')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        status_arr = ['2', '3', '5', '-1']
        offset = 0
        size = 20
        for arr in status_arr:
            while True:
                data = {
                    'status_list': arr,
                    'offset': offset,
                    'size': size
                }
                try:
                    headers = {'Content-Type': 'application/json'}
                    result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
                    result = json.loads(result.text)
                    logging.info("在职员工:{}".format(result))
                    if result.get('errcode') == 0:
                        d_res = result['result']
                        for data_list in d_res['data_list']:
                            sql = """UPDATE hr_employee SET work_status=2,office_status={} WHERE din_id='{}'""".format(data_list, arr)
                            self._cr.execute(sql)
                        if 'next_cursor' in d_res:
                            offset = d_res['next_cursor']
                        else:
                            break
                    else:
                        raise UserError("更新失败,原因:{}\r".format(result.get('errmsg')))
                except ReadTimeout:
                    raise UserError("网络连接超时")
        return True

    @api.model
    def get_querydimission(self):
        """
        更新离职员工
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'hrm_querydimission')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        offset = 0
        size = 50
        while True:
            data = {'offset': offset,'size': size}
            try:
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
                result = json.loads(result.text)
                logging.info("离职员工:{}".format(result))
                if result.get('errcode') == 0:
                    d_res = result['result']
                    for data_list in d_res['data_list']:
                        sql = """UPDATE hr_employee SET work_status=3 WHERE din_id='{}'""".format(data_list)
                        self._cr.execute(sql)
                    if 'next_cursor' in d_res:
                        offset = d_res['next_cursor']
                    else:
                        break
                else:
                    raise UserError("更新失败,原因:{}\r".format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时")
        return True

