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
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
import base64

_logger = logging.getLogger(__name__)


class AddDingDingEmployee(models.Model):
    _name = 'dingding.add.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '待入职员工'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    USERSTATE = [
        ('new', '创建'),
        ('lod', '待入职'),
        ('ing', '已入职')
    ]

    active = fields.Boolean(string=u'有效', default=True)
    user_id = fields.Char(string='钉钉用户Id')
    name = fields.Char(string='员工姓名', required=True)
    mobile = fields.Char(string='手机号', required=True)
    pre_entry_time = fields.Datetime(string=u'预期入职时间', required=True)
    dept_id = fields.Many2one(comodel_name='hr.department', string=u'入职部门', required=True)
    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id)
    image = fields.Binary("照片", default=_default_image, attachment=True)
    image_medium = fields.Binary("Medium-sized photo", attachment=True)
    image_small = fields.Binary("Small-sized photo", attachment=True)
    state = fields.Selection(string=u'状态', selection=USERSTATE, default='new', track_visibility='onchange')

    @api.model
    def create(self, values):
        tools.image_resize_images(values)
        return super(AddDingDingEmployee, self).create(values)

    @api.multi
    def write(self, values):
        tools.image_resize_images(values)
        return super(AddDingDingEmployee, self).write(values)

    @api.multi
    def add_employee(self):
        """
        添加待入职员工
        :return:
        """
        self.ensure_one()
        logging.info(">>>添加待入职员工start")
        url = self.env['dingding.parameter'].search([('key', '=', 'hrm_addpreentry')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        if not self.dept_id.ding_id:
            raise UserError("所选部门在钉钉中不存在!")
        user = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        data = {
            'param': {
                'name': self.name,
                'mobile': self.mobile,
                'pre_entry_time': str(self.pre_entry_time),
                'op_userid': user[0].ding_id if user else '',
                'extend_info': {'depts': self.dept_id.ding_id}
            }
        }
        try:
            headers = {'Content-Type': 'application/json'}
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
            result = json.loads(result.text)
            logging.info("添加待入职员工结果:{}".format(result))
            if result.get('errcode') == 0:
                self.write({
                    'user_id': result.get('userid'),
                    'state': 'lod'
                })
            else:
                raise UserError("添加失败,原因:{}!".format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时")
        logging.info(">>>添加待入职员工end")

    @api.multi
    def employees_have_joined(self):
        self.ensure_one()
        raise UserError("还没有做这个功能")
