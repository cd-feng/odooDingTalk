# -*- coding: utf-8 -*-
import datetime
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models, tools
from odoo.modules import get_module_resource
import base64

_logger = logging.getLogger(__name__)


class DingDingHealth(models.Model):
    _name = 'dingding.health'
    _description = '钉钉运动'
    _rec_name = 'emp_id'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    active = fields.Boolean(string=u'active', default=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)
    department_id = fields.Many2one('hr.department', string=u'部门', required=True)
    emp_id = fields.Many2one('hr.employee', string=u'员工', required=True)
    health_date = fields.Date(string=u'日期', required=True)
    health_count = fields.Integer(string=u'运动步数')
    image = fields.Binary("照片", default=_default_image, attachment=True)
    image_medium = fields.Binary("Medium-sized photo", attachment=True)
    image_small = fields.Binary("Small-sized photo", attachment=True)

    @api.model
    def create(self, values):
        tools.image_resize_images(values)
        return super(DingDingHealth, self).create(values)

    @api.multi
    def write(self, values):
        tools.image_resize_images(values)
        return super(DingDingHealth, self).write(values)

