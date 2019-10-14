# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng License(GNU)
###################################################################################

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HomeImages(models.Model):
    _name = 'applet.home.images'
    _description = "首页滚动图"
    _rec_name = 'name'
    _order = 'id'

    name = fields.Char(string='名称', index=True, required=True)
    url = fields.Char(string='图片URL', index=True, required=True)
    ttype = fields.Selection(string=u'类型', selection=[('image', '图片'), ('video', '视频')], default='image')
    active = fields.Boolean(string=u'有效', default=True, index=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', '名称已存在！'),
    ]


class EnterpriseDynamicTag(models.Model):
    _name = 'applet.enterprise.dynamic.tag'
    _description = "企业动态标签"
    _rec_name = 'name'
    _order = 'id'

    name = fields.Char(string='标签', index=True, required=True)


class EnterpriseDynamic(models.Model):
    _name = 'applet.enterprise.dynamic'
    _description = "企业动态"
    _rec_name = 'name'
    _order = 'id'

    name = fields.Char(string='标题', index=True, required=True)
    body = fields.Text(string=u'内容', index=True, required=True)
    tag_ids = fields.Many2many(comodel_name='applet.enterprise.dynamic.tag', string=u'标签')
    image = fields.Char(string='头图url地址')
    active = fields.Boolean(string=u'有效', default=True, index=True)

