# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt
_logger = logging.getLogger(__name__)


class SynchronousEmployee(models.TransientModel):
    _name = 'dingtalk.synchronous.employee'
    _description = '员工同步'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]

    company_ids = fields.Many2many('res.company', 'dingtalk_synchronous_employee_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.company.id])])
    repeat_type = fields.Selection(string=u'主键判断', selection=RepeatType, default='id')

    def on_synchronous(self):
        """
        同步员工信息
        :return:
        """
        self.ensure_one()
        self._synchronous_employee(self.company_ids.ids, self.repeat_type)

    def _synchronous_employee(self, company_ids, repeat_type):
        """
        处理同步员工信息
        :return:
        """
        start_time = datetime.now()  # 开始的时间
        for company_id in company_ids:
            company = self.env['res.company'].with_user(SUPERUSER_ID).search([('id', '=', company_id)], limit=1)
            dept_domain = [('ding_id', '!=', ''), ('company_id', '=', company.id)]
            departments = self.env['hr.department'].with_user(SUPERUSER_ID).search(dept_domain)
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            for department in departments:
                offset = 0
                size = 100
                while True:
                    if department.ding_id.find('-') != -1:
                        break
                    _logger.info(">>>开始获取%s部门的员工", department.name)
                    result_state = self._get_dingtalk_employee_list(client, department, offset, size,
                                                                    company, repeat_type)
                    if result_state:
                        offset = offset + 1
                    else:
                        break
        end_time = datetime.now()
        res_str = "同步员工完成，共用时：{}秒".format((end_time - start_time).seconds)
        _logger.info(res_str)

    def _get_dingtalk_employee_list(self, client, department, offset, size, company, repeat_type):
        """
        获取部门员工详情
        :return: 
        """
        try:
            result = client.user.list(department.ding_id, offset, size, order='custom')
            for user in result.get('userlist'):
                data = {
                    'name': user.get('name'),  # 员工名称
                    'ding_id': user.get('userid'),  # 钉钉用户Id
                    'din_unionid': user.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': user.get('mobile'),  # 手机号
                    'work_phone': user.get('mobile'),  # 分机号
                    'notes': user.get('remark'),  # 备注
                    'job_title': user.get('position'),  # 职位
                    'work_email': user.get('email'),  # email
                    'din_jobnumber': user.get('jobnumber'),  # 工号
                    'department_id': department.id,  # 部门
                    'ding_avatar_url': user.get('avatar') if user.get('avatar') else '',  # 钉钉头像url
                    'din_isSenior': user.get('isSenior'),  # 高管模式
                    'din_isAdmin': user.get('isAdmin'),  # 是管理员
                    'din_isBoss': user.get('isBoss'),  # 是老板
                    'din_isLeader': user.get('isLeader'),  # 是部门主管
                    'din_isHide': user.get('isHide'),  # 隐藏手机号
                    'din_active': user.get('active'),  # 是否激活
                    'din_isLeaderInDepts': user.get('isLeaderInDepts'),  # 是否为部门主管
                    'din_orderInDepts': user.get('orderInDepts'),  # 所在部门序位
                    'company_id': company.id
                }
                # 支持显示国际手机号
                if user.get('stateCode') != '86':
                    data.update({'mobile_phone': '+{}-{}'.format(user.get('stateCode'), user.get('mobile'))})
                if user.get('hiredDate'):
                    time_stamp = dt.timestamp_to_local_date(self, user.get('hiredDate'))
                    data.update({'hired_date': time_stamp})
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].with_user(SUPERUSER_ID).search([('ding_id', 'in', dep_din_ids), ('company_id', '=', company.id)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                if repeat_type == 'name':
                    domain = [('name', '=', user.get('name')), ('company_id', '=', company.id)]
                else:
                    domain = [('ding_id', '=', user.get('userid')), ('company_id', '=', company.id)]
                employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain)
                if employee:
                    employee.with_user(SUPERUSER_ID).write(data)
                else:
                    self.env['hr.employee'].with_user(SUPERUSER_ID).create(data)
            return result.get('hasMore')
        except Exception as e:
            raise exceptions.UserError(message="同步员工时发生异常：{}".format(str(e)))