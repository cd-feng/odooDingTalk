# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReturnApprovalState(models.TransientModel):
    _name = 'dingtalk.return.approval.state'
    _description = "恢复单据状态"

    APPROVALSTATE = [('draft', '草稿'), ('approval', '审批中'), ('stop', '审批结束')]
    APPROVALRESULT = [('load', '等待'), ('agree', '同意'), ('refuse', '拒绝'), ('redirect', '转交')]

    name = fields.Char(string="单据表名", required=True)
    res_id = fields.Integer(string="记录ID", required=True)
    dd_approval_state = fields.Selection(string="审批状态", selection=APPROVALSTATE, required=True, default='draft')
    dd_approval_result = fields.Selection(string="审批结果", selection=APPROVALRESULT, required=True, default='load')

    def confirm_return(self):
        """
        重置操作
        :return:
        """
        self.ensure_one()
        table_name = self.name.replace('.', '_')
        sql = """update {name} set dd_approval_state='{das}',dd_approval_result='{dar}',dd_doc_state='' where id={id}""" \
            .format(name=table_name, das=self.dd_approval_state, dar=self.dd_approval_result, id=self.res_id)
        _logger.info(sql)
        try:
            self._cr.execute(sql)
        except Exception as e:
            raise UserError("强制重置失败，原因为：{}".format(str(e)))