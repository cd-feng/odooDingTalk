# -*- coding: utf-8 -*-

import base64
import logging
import threading
import requests
from odoo import api, fields, models, exceptions, SUPERUSER_ID

UPDATEDINGTALKAVATARSTATE = False    # 替换头像的全局开关，防止重入
_logger = logging.getLogger(__name__)


class UpdateDingtalkEmployeeAvatar(models.TransientModel):
    _name = 'update.dingtalk.employee.avatar'
    _description = "替换员工头像"

    company_ids = fields.Many2many('res.company', 'dingtalk_update_employee_avatar_rel', string="同步的公司",
                                   required=True, default=lambda self: [(6, 0, [self.env.user.company_id.id])])

    def on_update(self):
        """
        确认替换头像
        :return:
        """
        self.ensure_one()
        global UPDATEDINGTALKAVATARSTATE
        if UPDATEDINGTALKAVATARSTATE:
            raise exceptions.ValidationError('系统正在后台替换所有员工的头像信息，请勿再次发起替换！')
        UPDATEDINGTALKAVATARSTATE = True    # 变为正在同步
        # 当前操作用户
        user_id = self.env.user.id
        t = threading.Thread(target=self._update_dingtalk_employee_avatar, args=(user_id, self.company_ids.ids))
        t.daemon = True
        t.start()
        return self.env.user.notify_success(message="系统正在后台替换员工头像，请耐心等待处理完成...")

    def _update_dingtalk_employee_avatar(self, user_id, company_ids):
        """
        执行替换操作
        :return:
        """
        # 由于主线程env已销毁，创建新env
        global UPDATEDINGTALKAVATARSTATE
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))

                user = self.env['res.users'].sudo().search([('id', '=', user_id)])
                user.notify_success(message="系统正在后台替换员工头像操作，请保持网络畅通！")
                for company_id in company_ids:
                    company = self.env['res.company'].sudo().search([('id', '=', company_id)], limit=1)

                    domain = [('company_id', '=', company.id), ('ding_avatar_url', '!=', False)]
                    employees = self.env['hr.employee'].sudo().search(domain)
                    employees_len = len(employees)
                    number = 1
                    for employee in employees:
                        _logger.info("%s >替换头像进度：%s / %s" % (company.name, number, employees_len))
                        try:
                            binary_data = base64.b64encode(requests.get(employee.ding_avatar_url).content)
                            employee.write({'image': binary_data})
                            number += 1
                        except Exception:
                            number += 1
                            continue
                # 完成后通知用户并修改全局设置
                UPDATEDINGTALKAVATARSTATE = False
                return user.notify_success(message="系统已成功替换{}位员工头像，请刷新界面！".format(number), sticky=True)

