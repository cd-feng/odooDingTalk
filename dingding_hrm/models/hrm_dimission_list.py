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

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingHrmDimissionList(models.Model):
    _name = 'dingding.hrm.dimission.list'
    _description = "离职员工信息"
    _rec_name = 'emp_id'

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
    emp_id = fields.Many2one(comodel_name='dingding.employee.roster',
                             string='员工')
    last_work_day = fields.Datetime(string='最后工作时间')
    reason_memo = fields.Text(string="离职原因")
    reason_type = fields.Selection(string='离职类型', selection=REASONTYPE)
    pre_status = fields.Selection(string='离职前工作状态', selection=PRESTATUS)
    handover_userid = fields.Many2one(
        comodel_name='hr.employee', string='离职交接人')


class GetDingDingHrmDimissionList(models.TransientModel):
    _name = 'dingding.get.hrm.dimission.list'
    _description = '获取离职员工信息'

    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_hrm_dimission_list_and_hr_employee_rel',
                               column1='list_id', column2='emp_id', string='员工', required=True)
    is_all_emp = fields.Boolean(string='全部离职员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search(
                [('ding_id', '!=', ''), ('work_status', '=', '3')])
            self.emp_ids = [(6, 0, emps.ids)]
        else:
            self.emp_ids = False

    @api.multi
    def get_hrm_dimission_list(self):
        """
        批量获取员工离职信息
        """
        logging.info(">>>获取钉钉获取离职员工信息start")
        ding_ids = list()
        for user in self.emp_ids:
            ding_ids.append(user.ding_id)
        user_list = self.env['hr.attendance.tran'].list_cut(ding_ids, 50)
        for u in user_list:
            self.dimission_list(u)
        logging.info(">>>获取钉钉获取离职员工信息end")
        action = self.env.ref(
            'dingding_hrm.dingding_hrm_dimission_list_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def dimission_list(self, user_ids):
        """
        批量获取员工离职信息
        根据传入的staffId列表，批量查询员工的离职信息
        :param userid_list: 员工id
        """
        din_client = self.env['dingding.api.tools'].get_client()
        logging.info(">>>获取钉钉获取离职员工信息start")
        if len(user_ids) > 50:
            raise UserError(_("钉钉仅支持批量查询小于等于50个员工!"))
        try:
            result = din_client.employeerm.listdimission(userid_list=user_ids)
            logging.info(">>>批量获取员工离职信息返回结果%s", result)
            if result.get('emp_dimission_info_vo'):
                for res in result.get('emp_dimission_info_vo'):
                    if res.get('main_dept_id'):
                        main_dept = self.env['hr.department'].search(
                            [('ding_id', '=', res.get('main_dept_id'))])
                    dept_list = list()
                    if res.get('dept_list'):
                        for depti in res['dept_list']['emp_dept_v_o']:
                            hr_dept = self.env['hr.department'].search(
                                [('ding_id', '=', depti.get('dept_id'))])
                            if hr_dept:
                                dept_list.append(hr_dept.id)
                    data = {
                        'ding_id': res.get('userid'),
                        'last_work_day': self.stamp_to_time(res.get('last_work_day')),
                        'department_ids': [(6, 0, dept_list)] if dept_list else '',
                        'reason_memo': res.get('reason_memo'),
                        'reason_type': str(res.get('reason_type')) if res.get('reason_type') else '9',
                        'pre_status': str(res.get('pre_status')),
                        'status': str(res.get('status')),
                        'main_dept_name': main_dept.id if main_dept else False,
                    }
                    if res.get('handover_userid'):
                        handover_userid = self.env['hr.employee'].search(
                            [('ding_id', '=', res.get('handover_userid'))])
                        data.update({'handover_userid': handover_userid.id})
                    emp = self.env['hr.employee'].search(
                        [('ding_id', '=', res.get('userid'))])
                    if emp:
                        data.update({'emp_id': emp[0].id})
                    hrm = self.env['dingding.hrm.dimission.list'].search(
                        [('ding_id', '=', res.get('userid'))])
                    if hrm:
                        hrm.write(data)
                    else:
                        self.env['dingding.hrm.dimission.list'].create(data)

        except Exception as e:
            raise UserError(e)
        logging.info(">>>获取获取离职员工信息end")

    @api.multi
    def get_hrm_employee_state(self):
        self.ensure_one()
        # 更新在职员工
        self.get_queryonjob()
        # 更新离职员工
        self.get_querydimission()

    @api.model
    def get_queryonjob(self):
        """
        更新在职员工,在职员工子状态筛选: 2，试用期；3，正式；5，待离职；-1，无状态
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        status_arr = ['2', '3', '5', '-1']
        for arr in status_arr:
            offset = 0
            size = 20
            while True:
                try:
                    result = din_client.employeerm.queryonjob(status_list=arr, offset=offset, size=size)
                    logging.info(">>>更新在职员工子状态[%s]返回结果%s", arr, result)
                    if result['data_list']:
                        result_list = result['data_list']['string']
                        for data_list in result_list:
                            sql = """UPDATE hr_employee SET work_status='2',office_status={} WHERE ding_id='{}'""".format(
                                arr, data_list)
                            self._cr.execute(sql)
                        if 'next_cursor' in result:
                            offset = result['next_cursor']
                        else:
                            break
                    else:
                        break
                except Exception as e:
                    raise UserError(e)
        return True

    @api.model
    def get_querydimission(self):
        """
        更新离职员工
        :return:
        """
        din_client = self.env['dingding.api.tools'].get_client()
        offset = 0
        size = 50
        while True:
            try:
                result = din_client.employeerm.querydimission(offset=offset, size=size)
                logging.info(">>>获取离职员工列表返回结果%s", result)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    self.dimission_list(result_list)
                    for data_list in result_list:
                        sql = """UPDATE hr_employee SET work_status='3' WHERE ding_id='{}'""".format(data_list)
                        self._cr.execute(sql)
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                    else:
                        break
                else:
                    break
            except Exception as e:
                raise UserError(e)
        return True

    @api.model
    def get_dimission_list(self):
        """
        获取离职员工列表
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

    def stamp_to_time(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000)
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
