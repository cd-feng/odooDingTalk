# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class TransferMethod(models.Model):
    _name = 'stock.transfer.method'
    _description = "调拨方式"
    _rec_name = 'name'

    name = fields.Char(string='名称', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'已存在相同调拨方式!'),
    ]


class BankChannel(models.Model):
    _name = 'stock.bank.channel'
    _description = "银行渠道"
    _rec_name = 'name'

    name = fields.Char(string='名称', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'已存在相同银行渠道!'),
    ]


class DeliveryMethod(models.Model):
    _name = 'stock.delivery.method'
    _description = "货运方式"
    _rec_name = 'name'

    name = fields.Char(string='名称', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'已存在相同货运方式!'),
    ]
