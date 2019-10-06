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
import base64
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.modules import get_module_resource

_logger = logging.getLogger(__name__)


class AddDingDingEmployee(models.Model):
    _name = 'dingding.add.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '待入职员工'

    @api.model
    def _default_image(self):
        image_path = get_module_resource(
            'hr', 'static/src/img', 'default_image.png')
        return base64.b64encode(open(image_path, 'rb').read())

    USERSTATE = [
        ('new', '创建'),
        ('lod', '待入职'),
        ('ing', '已入职')
    ]

    active = fields.Boolean(string='有效', default=True)
    user_id = fields.Char(string='钉钉用户Id')
    name = fields.Char(string='员工姓名', required=True)
    mobile = fields.Char(string='手机号', required=True)
    pre_entry_time = fields.Datetime(string='预期入职时间', required=True)
    dept_id = fields.Many2one(comodel_name='hr.department', string='入职部门')
    company_id = fields.Many2one(
        'res.company', '公司', default=lambda self: self.env.user.company_id.id)
    image = fields.Binary("照片", default=_default_image, attachment=True)
    image_medium = fields.Binary("Medium-sized photo", attachment=True)
    image_small = fields.Binary("Small-sized photo", attachment=True)
    state = fields.Selection(
        string='状态', selection=USERSTATE, default='new', track_visibility='onchange')

    @api.model
    def create(self, values):
        tools.image_resize_images(values)
        return super(AddDingDingEmployee, self).create(values)

    def write(self, values):
        tools.image_resize_images(values)
        return super(AddDingDingEmployee, self).write(values)

    def add_employee(self):
        """
        智能人事添加企业待入职员工

        :param param: 添加待入职入参
        """
        din_client = self.env['dingding.api.tools'].get_client()
        self.ensure_one()
        logging.info(">>>添加待入职员工start")
        user = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)])
        name = self.name
        mobile = self.mobile
        pre_entry_time = self.pre_entry_time
        op_userid = user[0].ding_id if user else ''
        extend_info = {'depts': self.dept_id.ding_id} if self.dept_id else ''
        try:
            result = din_client.employeerm.addpreentry(
                name, mobile, pre_entry_time=pre_entry_time, op_userid=op_userid, extend_info=extend_info)
            logging.info(">>>添加待入职员工返回结果%s", result)
            self.write({
                'user_id': result.get('userid'),
                'state': 'lod'
            })
        except Exception as e:
            raise UserError(e)
        logging.info(">>>添加待入职员工end")

    @api.model
    def count_pre_entry(self):
        """
        智能人事查询公司待入职员工列表,返回待入职总人数
        智能人事业务，企业/ISV分页查询公司待入职员工id列表

        :param offset: 分页起始值，默认0开始
        :param size: 分页大小，最大50
        """
        din_client = self.env['dingding.api.tools'].get_client()
        try:
            result = din_client.employeerm.querypreentry(offset=0, size=50)
            logging.info(">>>查询待入职员工列表返回结果%s", result)
            if result['data_list']['string']:
                pre_entry_list = result['data_list']['string']
                return len(pre_entry_list)
        except Exception as e:
            raise UserError(e)

    def employees_have_joined(self):
        self.ensure_one()
        raise UserError(_("还没有做这个功能"))
