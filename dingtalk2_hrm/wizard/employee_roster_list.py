# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import threading
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt

_logger = logging.getLogger(__name__)
SynchronousDingTalkRosterList = False

# 要同步的字段列表
FieldFilterList = [
    'sys00-name',
    'sys00-email',
    'sys00-deptIds',
    'sys00-mainDeptId',
    'sys00-dept',
    'sys00-mainDept',
    'sys00-position',
    'sys00-mobile',
    'sys00-jobNumber',
    'sys00-tel',
    'sys00-workPlace',
    'sys00-remark',
    'sys00-confirmJoinTime',
    'sys01-employeeType',
    'sys01-employeeStatus',
    'sys01-probationPeriodType',
    'sys01-planRegularTime',
    'sys01-regularTime',
    'sys01-positionLevel',
    'sys02-realName',
    'sys02-certNo',
    'sys02-birthTime',
    'sys02-sexType',
    'sys02-nationType',
    'sys02-certAddress',
    'sys02-certEndTime',
    'sys02-marriage',
    'sys02-joinWorkingTime',
    'sys02-residenceType',
    'sys02-address',
    'sys02-politicalStatus',
    'sys09-personalSi',
    'sys09-personalHf',
    'sys03-highestEdu',
    'sys03-graduateSchool',
    'sys03-graduationTime',
    'sys03-major',
    'sys04-bankAccountNo',
    'sys04-accountBank',
    'sys05-contractCompanyName',
    'sys05-contractType',
    'sys05-firstContractStartTime',
    'sys05-firstContractEndTime',
    'sys05-nowContractStartTime',
    'sys05-contractRenewCount',
    'sys06-urgentContactsName',
    'sys06-urgentContactsRelation',
    'sys06-urgentContactsPhone',
    'sys07-haveChild',
]


class EmployeeRosterSynchronous(models.TransientModel):
    _name = 'dingtalk.employee.roster.synchronous'
    _description = "智能人事花名册同步"

    company_ids = fields.Many2many("res.company", string="同步的公司", required=True, default=lambda self: [(6, 0, [self.env.company.id])])

    def start_synchronous_data(self):
        """
        花名册同步
        :return:
        """
        self.ensure_one()
        global SynchronousDingTalkRosterList
        if SynchronousDingTalkRosterList:
            raise exceptions.UserError('系统后台正在同步花名册数据，请勿再次发起！')
        SynchronousDingTalkRosterList = True  # 变为正在同步
        # 当前操作用户
        user_id = self.env.user.id
        t = threading.Thread(target=self._synchronous_roster_list, args=(user_id, self.company_ids.ids))
        t.start()
        # return self.env.user.notify_success(message="系统后台正在同步花名册数据，请耐心等待处理完成...")

    def _synchronous_roster_list(self, user_id, company_ids):
        """
        同步花名册信息
        :param user_id:
        :param company_ids:
        :return:
        """
        global SynchronousDingTalkRosterList
        with self.pool.cursor() as cr:
            self = self.with_env(self.env(cr=cr))
            start_time = datetime.now()  # 开始的时间
            user = self.env['res.users'].with_user(SUPERUSER_ID).search([('id', '=', user_id)])
            for company_id in company_ids:
                company = self.env['res.company'].with_user(SUPERUSER_ID).search([('id', '=', company_id)], limit=1)
                client = dt.get_client(self, dt.get_dingtalk2_config(self, company))
                # self.get_field_group_list(client, company)
                # 获取在职员工列表
                queryonjob_roster_list = self.get_queryonjob_roster_list(company, user)
                # # 获取待入职员工列表
                querypreentry_roster_list = self.get_querypreentry_roster_list(company, user)
                userid_list = queryonjob_roster_list + querypreentry_roster_list
                self.create_employee_roster(client, dt.list_cut(userid_list, 20), company.id, user)
            SynchronousDingTalkRosterList = False
            res_str = "获取员工花名册数据处理完成，共用时：{}秒".format((datetime.now() - start_time).seconds)
            _logger.info(res_str)
            # return user.notify_success(message=res_str, sticky=True)

    def get_field_group_list(self, client, company_id):
        """
        获取花名册字段组详情
        :return:
        """
        try:
            req_result = client.post('topapi/smartwork/hrm/employee/field/grouplist', {
                'agentid': dt.get_agent_id(self, company_id)
            })
            if req_result.get('errcode') != 0:
                print(req_result.get('errmsg'))
                return False
            else:
                for result in req_result.get('result'):
                    for field_list in result.get('field_list'):
                        print(field_list)
        except Exception as e:
            return False

    def get_queryonjob_roster_list(self, company_id, user_id=None):
        """
        获取在职员工列表
        :param company_id:
        :param user_id:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
        onjob_list = list()
        status_list = '2,3,5,-1'  # 在职员工子状态筛选。2，试用期；3，正式；5，待离职；-1，无状态
        offset = 0  # 分页起始值，默认0开始
        size = 50   # 分页大小，最大50
        while True:
            try:
                result = client.employeerm.queryonjob(status_list=status_list, offset=offset, size=size)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    onjob_list.extend(result_list)
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                    else:
                        break
                else:
                    break
            except Exception as e:
                _logger.info("同步在职员工失败：{}".format(str(e)))
                return onjob_list
        return onjob_list

    def get_querypreentry_roster_list(self, company, user=None):
        """
        获取待入职员工列表
        :param company:
        :param user:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company))
        value_list = list()
        offset = 0  # 分页起始值，默认0开始
        while True:
            try:
                req_result = client.post('topapi/smartwork/hrm/employee/querypreentry', {
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
                # if user:
                    # user.notify_success(message="同步待入职员工列表失败：{}".format(str(e)), sticky=True)
                _logger.info("同步待入职员工列表失败：{}".format(str(e)))
                return value_list
        return value_list

    def create_employee_roster(self, client, user_list, company_id, user=None):
        """
        获取钉钉在职员工花名册
        :param client:
        :param user_list:
        :param company_id:
        :param user:
        :return:
        """
        for user_cut in user_list:
            _logger.info(">>>同步员工列表的花名册: {}".format(user_cut))
            roster_model = self.env['dingtalk.employee.roster']
            roster_fields = roster_model._fields
            try:
                # result = client.employeerm.list(user_cut, field_filter_list=FieldFilterList)
                result = client.employeerm.list(user_cut)
                if result.get('emp_field_info_v_o'):
                    for rec in result.get('emp_field_info_v_o'):
                        roster_data = {
                            'ding_userid': rec['userid'],
                            'company_id': company_id
                        }
                        for fie in rec['field_list']['emp_field_v_o']:
                            if fie['field_code'][6:] not in roster_fields:
                                continue
                            # 检查相关字段
                            if fie['field_code'] == 'sys00-name':
                                roster_data['name'] = fie.get('label')
                            # 获取部门（可能会多个）
                            elif fie['field_code'][6:] == 'deptIds':
                                if 'value' not in fie:
                                    continue
                                dept_ding_ids = fie['value'].split('|')
                                domain = [('company_id', '=', company_id), ('ding_id', 'in', dept_ding_ids)]
                                departments = self.env['hr.department'].with_user(SUPERUSER_ID).search(domain)
                                if departments:
                                    roster_data.update({'dept': [(6, 0, departments.ids)]})
                            # 获取主部门
                            elif fie['field_code'][6:] == 'mainDeptId':
                                if 'value' not in fie:
                                    continue
                                domain = [('company_id', '=', company_id), ('ding_id', '=', fie['value'])]
                                dept = self.env['hr.department'].with_user(SUPERUSER_ID).search(domain, limit=1)
                                if dept:
                                    roster_data.update({'mainDept': dept.id})
                            elif fie['field_code'][6:] == 'dept' or fie['field_code'][6:] == 'mainDept':
                                continue
                            # 同步工作岗位
                            elif fie['field_code'][6:] == 'position':
                                if 'label' not in fie:
                                    continue
                                domain = [('company_id', '=', company_id), ('name', '=', fie['label'])]
                                hr_job = self.env['hr.job'].with_user(SUPERUSER_ID).search(domain, limit=1)
                                if not hr_job and fie.get('label'):
                                    hr_job = self.env['hr.job'].with_user(SUPERUSER_ID).create({'name': fie.get('label'), 'company_id': company_id})
                                roster_data.update({'position': hr_job.id or False})
                            # 发薪公司
                            elif fie['field_name'] == '发薪公司':
                                roster_data['salaryCompanyName'] = fie.get('label')
                            else:
                                if "label" in fie and fie.get('label') != '#VALUE!':
                                    f_value = fie.get('label')
                                else:
                                    f_value = False
                                roster_data.update({
                                    fie['field_code'][6:]: f_value
                                })
                        domain = [('company_id', '=', company_id), ('ding_userid', '=', rec['userid'])]
                        roster = self.env['dingtalk.employee.roster'].with_user(SUPERUSER_ID).search(domain)
                        if roster:
                            roster.write(roster_data)
                        else:
                            self.env['dingtalk.employee.roster'].with_user(SUPERUSER_ID).create(roster_data)
                else:
                    # if user:
                    #     user.notify_warning(message="获取花名册失败,原因:{}".format(result.get('errmsg')), sticky=True)
                    _logger.info("获取花名册失败,原因:{}".format(result.get('errmsg')))
            except Exception as e:
                # if user:
                #     user.notify_warning(message="同步员工花名册信息失败：{}".format(str(e)), sticky=True)
                _logger.info("同步员工花名册信息失败：{}".format(str(e)))

    def get_employee_field_grouplist(self, company_id):
        """
        获取花名册元数据
        这里只是测试的应用的，检查了下钉钉里面有哪些字段
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk2_config(self, company_id))
        try:
            req_result = client.post('topapi/smartwork/hrm/roster/meta/get', {
                'agentid': dt.get_agent_id(self, company_id),
            })
            result_list = req_result['result']
            for result in result_list:
                print(result)
        except Exception as e:
            _logger.info("获取花名册元数据失败：{}".format(str(e)))

    # ------定时任务------
    def get_hrm_employee_roster(self):
        """
        定时任务： 同步员工花名册数据
        :return:
        """
        configs = self.env['dingtalk.config'].sudo().search([('auto_get_emp_roster', '=', True)])
        for config in configs:
            client = dt.get_client(self, dt.get_dingtalk2_config(self, config.company_id))
            # 获取在职员工列表
            queryonjob_roster_list = self.get_queryonjob_roster_list(config.company_id)
            # 获取待入职员工列表
            querypreentry_roster_list = self.get_querypreentry_roster_list(config.company_id)
            userid_list = queryonjob_roster_list + querypreentry_roster_list
            self.create_employee_roster(client, dt.list_cut(userid_list, 20), config.company_id.id)

    def synchronize_employees_system(self):
        """
        定时任务：更新花名册数据至系统员工
        :return:
        """
        configs = self.env['dingtalk.config'].sudo().search([('auto_sync_employees_system', '=', True)])
        for config in configs:
            rosters = self.env['dingtalk.employee.roster'].search([('company_id', '=', config.company_id.id)])
            for roster in rosters:
                if roster.employee_id:
                    # 将花名册中的数据写入到员工中
                    value = {
                        'identification_id': roster.certNo,  # 证件号码
                        'work_email': roster.email,  # 邮箱
                    }
                    if roster.sexType == '男':
                        value['gender'] = 'male'
                    elif roster.sexType == '女':
                        value['gender'] = 'female'
                    roster.employee_id.write(value)
