# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EmployeeRosterReport(models.AbstractModel):
    _name = 'dingtalk.employee.roster.report'
    _description = "打印花名册"

    def _get_report_values(self, docids, data=None):
        docs = self.env['dingtalk.employee.roster'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'data': data,
        }
