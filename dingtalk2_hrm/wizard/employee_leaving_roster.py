# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt

_logger = logging.getLogger(__name__)


class EmployeeRosterLeaving(models.TransientModel):
    _name = 'dingtalk.employee.roster.leaving'
    _description = "同步离职员工信息"

    def get_hrm_dimission_list(self):
        """
        定时任务： 定时获取所有离职员工信息
        :return:
        """
        configs = self.env['dingtalk.config'].sudo().search([('is_get_dimission_hrm', '=', True)])
        for config in configs:
            _logger.info("开始处理<{}>的离职员工数据".format(config.company_id.name))
            dimission_list = self.get_querydimission_list(config.company_id)
            self.get_listdimission_info(dimission_list, config.company_id)
            _logger.info("<{}>的离职员工数据处理完成".format(config.company_id.name))
            self._cr.commit()

    def get_querydimission_list(self, company_id):
        """
        获取离职员工列表
        :param company_id:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
        value_list = list()
        offset = 0  # 分页起始值，默认0开始
        while True:
            try:
                req_result = client.post('topapi/smartwork/hrm/employee/querydimission', {
                    'offset': offset,
                    'size': 50,
                })
                result = req_result['result']
                value_list.extend(result.get('data_list'))
                if 'next_cursor' in result:
                    offset = result.get('next_cursor')
                else:
                    break
            except Exception as e:
                _logger.info("钉钉花名册：同步离职员工列表失败，原因：{}".format(e))
                break
        # 排除掉不再当前花名册中出现的员工
        domain = [('company_id', '=', company_id.id), ('ding_userid', 'in', value_list)]
        rosters = self.env['dingtalk.employee.roster'].sudo().search(domain)
        leaving_emp_list = []
        for roster in rosters:
            leaving_emp_list.append(roster.ding_userid)
        return leaving_emp_list

    def get_listdimission_info(self, dimission_list, company_id):
        """
        同步离职员工信息
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk_config(self, company_id))
        leaving_user_list = dt.list_cut(dimission_list, 50)
        for leaving_users in leaving_user_list:
            userid_list = str()
            for leaving_id in leaving_users:
                if userid_list:
                    userid_list = "{},{}".format(userid_list, leaving_id)
                else:
                    userid_list = leaving_id
            req_result = client.post('topapi/smartwork/hrm/employee/listdimission', {
                'userid_list': userid_list,
            })
            for result in req_result.get('result'):
                user_id = result.get('userid')
                domain = [('company_id', '=', company_id.id), ('ding_userid', '=', user_id)]
                rosters = self.env['dingtalk.employee.roster'].sudo().search(domain)
                if not rosters:
                    continue
                value = {
                    'company_id': company_id.id,
                    'employeeStatus': '离职',
                    'reason_memo': result.get('reason_memo'),
                    'main_dept_name': result.get('main_dept_name'),
                    'main_dept_id': result.get('main_dept_id'),
                }
                if result.get('handover_userid'):
                    handover_userid = self.env['hr.employee'].search([('ding_id', '=', result.get('handover_userid'))])
                    if handover_userid:
                        value['handover_userid'] = handover_userid[0].id
                if result.get('last_work_day'):
                    value['last_work_day'] = dt.timestamp_to_local_date(self, result.get('last_work_day'))
                if result.get('reason_type'):
                    value['reason_type'] = str(result.get('reason_type'))
                if result.get('pre_status'):
                    value['pre_status'] = str(result.get('pre_status'))
                if result.get('status'):
                    value['status'] = str(result.get('status'))
                rosters.write(value)


