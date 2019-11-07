# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _name = 'hr.department'

    ding_id = fields.Char(string='钉钉Id', index=True)
    ding_sy_state = fields.Boolean(string=u'钉钉同步标识', default=False, help="避免使用同步时,会执行创建、修改上传钉钉方法")
    manager_user_ids = fields.Many2many('hr.employee', 'hr_department_manage_user_employee_rel', string=u'主管')
    is_root = fields.Boolean(string=u'根部门?', default=False)

    def create_ding_department(self):
        self.ensure_one()
        client = dingtalk_api.get_client()
        for res in self:
            if res.ding_id:
                raise UserError("该部门已在钉钉ID已存在，不能在进行上传。  *_*！")
            data = {'name': res.name}  # 部门名称
            # 获取父部门ding_id
            if res.is_root:
                data.update({'parentid': 1})
            else:
                if res.parent_id:
                    data.update({'parentid': res.parent_id.ding_id if res.parent_id.ding_id else ''})
                else:
                    raise UserError("请选择上级部门或则根部门。 *_*!")
            try:
                result = client.department.create(data)
                res.write({'ding_id': result})
                res.message_post(body=u"上传钉钉成功。 *_*!", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def update_ding_department(self):
        self.ensure_one()
        client = dingtalk_api.get_client()
        for res in self:
            data = {
                'id': res.ding_id,  # id
                'name': res.name,  # 部门名称
                'parentid': res.parent_id.ding_id,  # 父部门id
            }
            if res.is_root:
                data.update({'parentid': 1})
            try:
                result = client.department.update(data)
                _logger.info(_("已在钉钉上更新Id:{}的部门".format(result)))
                res.message_post(body=u"更新钉钉部门成功。 *_*!", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def delete_ding_department(self):
        self.ensure_one()
        for res in self:
            if not res.ding_id:
                continue
            self._delete_dingtalk_department_by_id(res.ding_id)
            res.write({'ding_id': False})
            res.message_post(body=u"已在钉钉上删除部门。 *_*!", message_type='notification')
        return {'type': 'ir.actions.act_window_close'}

    def unlink(self):
        for res in self:
            if res.ding_id:
                self._delete_dingtalk_department_by_id(res.ding_id)
            super(HrDepartment, self).unlink()

    def _delete_dingtalk_department_by_id(self, ding_id):
        client = dingtalk_api.get_client()
        try:
            result = client.department.delete(ding_id)
            _logger.info(_("已在钉钉上删除Id:{}的部门".format(result)))
        except Exception as e:
            raise UserError(e)
        return
