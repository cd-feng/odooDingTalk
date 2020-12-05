# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###################################################################################
import datetime
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class UserCheckIn(models.Model):
    _name = 'hcm.user.checkin'
    _description = "用户签到"
    _rec_name = 'emp_id'
    _order = 'id'

    active = fields.Boolean(string=u'有效', default=True)
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', index=True, required=True)
    check_time = fields.Datetime(string=u'签到时间', required=True, default=fields.datetime.now())
    check_date = fields.Date(string=u'签到日期', default=fields.date.today())
    time_type = fields.Selection(string=u'时间类型', selection=[('in', '上班卡'), ('out', '下班卡')], index=True)
    check_type = fields.Selection(string=u'签到类型', selection=[('normal', '正常打卡'), ('field', '外勤打卡')], default='normal')
    location = fields.Char(string='签到地点')
    description = fields.Char(string='外勤描述')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='附件')

    def attachment_image_preview(self):
        self.ensure_one()
        domain = [('res_model', '=', self._name), ('res_id', '=', self.id)]
        return {
            'domain': domain,
            'res_model': 'ir.attachment',
            'name': u'附件管理',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 20,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.constrains('check_time')
    def _constrains_check_time(self):
        """
        :return:
        """
        for res in self:
            check_time = res.check_time
            if check_time:
                res.check_date = str(check_time)[:10]
                check_time = check_time + datetime.timedelta(hours=8)
                if check_time.hour <= 12:
                    res.time_type = 'in'
                else:
                    res.time_type = 'out'
