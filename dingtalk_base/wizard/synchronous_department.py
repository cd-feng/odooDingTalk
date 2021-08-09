# -*- coding: utf-8 -*-

import logging
import threading
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt
_logger = logging.getLogger(__name__)

SYNCHRONOUSDINGTALKDEPT = False


class SynchronousDepartment(models.TransientModel):
    _name = 'dingtalk.synchronous.department'
    _description = '部门同步'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]

    company_ids = fields.Many2many('res.company', 'dingtalk_synchronous_department_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.company.id])])
    repeat_type = fields.Selection(string=u'主键判断', selection=RepeatType, default='id')

    def on_synchronous(self):
        """
        同步部门信息
        :return:
        """
        self.ensure_one()
        global SYNCHRONOUSDINGTALKDEPT
        if SYNCHRONOUSDINGTALKDEPT:
            raise exceptions.UserError('系统正在后台同步部门信息，请勿再次发起！')
        SYNCHRONOUSDINGTALKDEPT = True  # 变为正在同步
        # 当前操作用户
        user_id = self.env.user.id
        t = threading.Thread(target=self._synchronous_department, args=(user_id, self.company_ids.ids))
        t.start()
        return self.env.user.notify_success(message="系统正在后台同步部门信息，请耐心等待处理完成...")

    def _synchronous_department(self, user_id, company_ids):
        """
        异步处理同步部门信息
        :return:
        """
        global SYNCHRONOUSDINGTALKDEPT
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                start_time = datetime.now()  # 开始的时间

                user = self.env['res.users'].with_user(SUPERUSER_ID).search([('id', '=', user_id)])
                for company_id in company_ids:
                    company = self.env['res.company'].with_user(SUPERUSER_ID).search([('id', '=', company_id)], limit=1)
                    try:
                        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
                        result = client.department.list(fetch_child=True)
                    except Exception as e:
                        SYNCHRONOUSDINGTALKDEPT = False
                        return user.notify_success(message="同步部门时发生异常，原因为：{}".format(str(e)), sticky=True)
                    number = 1
                    for res in result:
                        _logger.info("正在处理第%s条数据，-> %s" % (number, res))
                        data = {
                            'company_id': company.id,
                            'name': res.get('name'),
                            'ding_id': res.get('id'),
                        }
                        if self.repeat_type == 'name':
                            domain = [('name', '=', res.get('name')), ('company_id', '=', company.id)]
                        else:
                            domain = [('ding_id', '=', res.get('id')), ('company_id', '=', company.id)]
                        h_department = self.env['hr.department'].search(domain)
                        if h_department:
                            h_department.write(data)
                        else:
                            self.env['hr.department'].create(data)
                        number += 1
                SYNCHRONOUSDINGTALKDEPT = False
                end_time = datetime.now()
                res_str = "同步部门完成，共用时：{}秒".format((end_time - start_time).seconds)
                _logger.info(res_str)
                return user.with_user(SUPERUSER_ID).notify_success(message=res_str, sticky=True)
