# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, SUPERUSER_ID, exceptions
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt

_logger = logging.getLogger(__name__)


class HrmEmployeeRosterAdd(models.TransientModel):
    _name = 'dingtalk.addpreentry.roster'
    _description = "添加待入职员工"

    EMPLOYEETYPES = [
        ('0', '无类型'), ('1', '全职'), ('2', '兼职'), ('3', '实习'),
        ('4', '劳务派遣'), ('5', '退休返聘'), ('6', '劳务外包'),
    ]
    name = fields.Char(string="员工名称", required=True)
    mobile = fields.Char(string="手机号码", required=True)
    pre_entry_time = fields.Datetime(string="预期入职时间", required=True)
    mainDeptId = fields.Many2one('hr.department', string='入职部门')
    job_id = fields.Many2one(comodel_name="hr.job", string="职位")
    din_jobnumber = fields.Char(string='工号')
    employeeType = fields.Selection(string='员工类型', selection=EMPLOYEETYPES)
    op_userid = fields.Many2one(comodel_name="hr.employee", string="操作人", required=True)

    def on_ok(self):
        """
        确认添加
        :return:
        """
        self.ensure_one()
        try:
            client = dt.get_client(self, dt.get_dingtalk2_config(self, self.env.company))
            req_result = client.post('topapi/smartwork/hrm/employee/addpreentry', {
                'param': {
                    'name': self.name,
                    'pre_entry_time': self.pre_entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'mobile': self.mobile,
                    'op_userid': self.op_userid.ding_id
                },
            })
        except Exception as e:
            raise exceptions.UserError("添加失败，原因为:{}".format(str(e)))
        if req_result.get('errcode') == 0:
            self.env.user.notify_warning(message="已成功添加待入职员工：{}".format(self.name), sticky=False)
            user_id = req_result.get('userid')
            result = self.env['dingtalk.employee.roster'].search([('company_id', '=', self.env.company.id), ('ding_userid', '=', user_id)])
            if not result:
                self.env['dingtalk.employee.roster'].create({
                    'ding_userid': user_id,
                    'name': self.name,
                    'mobile': self.mobile,
                })
        else:
            raise exceptions.UserError("添加失败，原因为:{}".format(req_result.get('errmsg')))
