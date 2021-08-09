# -*- coding: utf-8 -*-

import logging
import threading
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt
_logger = logging.getLogger(__name__)

SYNCHRONOUSDINGTALKEMP = False


class SynchronousEmployee(models.TransientModel):
    _name = 'dingtalk.synchronous.employee'
    _description = '员工同步'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]

    company_ids = fields.Many2many('res.company', 'dingtalk_synchronous_employee_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.user.company_id.id])])
    repeat_type = fields.Selection(string=u'主键判断', selection=RepeatType, default='id')

    def on_synchronous(self):
        """
        同步员工信息
        :return:
        """
        self.ensure_one()
        global SYNCHRONOUSDINGTALKEMP
        if SYNCHRONOUSDINGTALKEMP:
            raise exceptions.UserError('系统正在后台同步员工信息，请勿再次发起！')
        SYNCHRONOUSDINGTALKEMP = True  # 变为正在同步
        # 当前操作用户
        user_id = self.env.user.id
        t = threading.Thread(target=self._synchronous_employee, args=(user_id, self.company_ids.ids, self.repeat_type))
        t.start()
        return self.env.user.notify_success(message="系统正在后台同步员工信息，请耐心等待处理完成...")

    def _synchronous_employee(self, user_id, company_ids, repeat_type):
        """
        异步处理同步员工信息
        :return:
        """
        global SYNCHRONOUSDINGTALKEMP
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                start_time = datetime.now()  # 开始的时间
                user = self.env['res.users'].sudo().search([('id', '=', user_id)])
                for company_id in company_ids:
                    company = self.env['res.company'].sudo().search([('id', '=', company_id)], limit=1)
                    dept_domain = [('ding_id', '!=', ''), ('company_id', '=', company.id)]
                    departments = self.env['hr.department'].sudo().search(dept_domain)
                    client = dt.get_client(self, dt.get_dingtalk_config(self, company))
                    for department in departments:
                        offset = 0
                        size = 100
                        while True:
                            if department.ding_id.find('-') != -1:
                                break
                            _logger.info(">>>开始获取%s部门的员工", department.name)
                            result_state = self._get_dingtalk_employee_list(client, department, offset, size,
                                                                            company, repeat_type, user)
                            if result_state:
                                offset = offset + 1
                            else:
                                break
                SYNCHRONOUSDINGTALKEMP = False
                end_time = datetime.now()
                res_str = "同步员工完成，共用时：{}秒".format((end_time - start_time).seconds)
                _logger.info(res_str)
                return user.notify_success(message=res_str, sticky=True)

    def _get_dingtalk_employee_list(self, client, department, offset, size, company, repeat_type, user_id):
        """
        获取部门员工详情
        :return: 
        """
        global SYNCHRONOUSDINGTALKEMP
        try:
            result = client.user.list(department.ding_id, offset, size, order='custom')
            for user in result.get('userlist'):
                data = {
                    'name': user.get('name'),  # 员工名称
                    'ding_id': user.get('userid'),  # 钉钉用户Id
                    'din_unionid': user.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': user.get('mobile'),  # 手机号
                    'work_phone': user.get('mobile'),  # 分机号
                    'work_location': user.get('workPlace'),  # 办公地址
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
                    dep_list = self.env['hr.department'].sudo().search([('ding_id', 'in', dep_din_ids), ('company_id', '=', company.id)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                if repeat_type == 'name':
                    domain = [('name', '=', user.get('name')), ('company_id', '=', company.id)]
                else:
                    domain = [('ding_id', '=', user.get('userid')), ('company_id', '=', company.id)]
                employee = self.env['hr.employee'].sudo().search(domain)
                if employee:
                    employee.sudo().write(data)
                else:
                    self.env['hr.employee'].sudo().create(data)
            return result.get('hasMore')
        except Exception as e:
            SYNCHRONOUSDINGTALKEMP = False
            user_id.sudo().notify_warning(message="同步员工时发生异常：{}".format(str(e)), sticky=True)
            return False
