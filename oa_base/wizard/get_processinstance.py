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
import json
import logging
import requests
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GetProcessInstance(models.TransientModel):
    _name = 'oa.get.process.instance'
    _description = "获取审批实例"

    oa_madel = fields.Many2one(comodel_name='dingding.approval.template', string=u'审批模型')
    start_time = fields.Datetime(string=u'开始时间')
    end_time = fields.Datetime(string=u'结束时间')

    @api.multi
    def get_process_list(self):
        """
        根据选择的审批模型批量获取实例id，再通过实例id去获取实例详情
        :return:
        """
        self.ensure_one()
        # 检查选择的审批模型是否已关联odoo单据
        dac = self.env['dingding.approval.control'].search([('template_id', '=', self.oa_madel.id)], limit=1)
        if not dac:
            raise UserError("该审批模型没有关联Odoo单据，请先进行关联后再来操作！")
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('processinstance_listids')
        size = 20
        cursor = 0
        start_time = str(self.env['dingding.api.tools'].datetime_to_stamp(self.start_time))[:13]
        end_time = str(self.env['dingding.api.tools'].datetime_to_stamp(self.end_time))[:13]
        process_list = list()    # 实例数组
        while True:
            data = {
                'process_code': self.oa_madel.process_code,
                'start_time': start_time,
                'end_time': end_time,
                'size': size,
                'cursor': cursor,
            }
            result = self.env['dingding.api.tools'].send_post_request(url, token, data, 15)
            r_result = result.get('result')
            for arr in r_result.get('list'):
                process_list.append(arr)
            if 'next_cursor' not in r_result:
                break
            cursor = r_result.get('next_cursor')
        # 批量获取实例详情
        self._get_process_info(process_list, dac.oa_model_id)

    @api.model
    def _get_process_info(self, process_list, odoo_model):
        """
        获取实例详情并写入到相应的表单
        :param process_list:  审批实例ids  数组
        :param odoo_model:  odoo模型
        :return:
        """
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('processinstance_get')
        for process_id in process_list:
            data = {'process_instance_id': process_id}
            result = self.env['dingding.api.tools'].send_post_request(url, token, data, 20)
            print(result)
        print(odoo_model.name)
        print(odoo_model._name)
        print(odoo_model.model)
        return True

{
    'process_instance': {
        'originator_userid': '2660205649-53768585',  # 发起人
        'originator_dept_name': '实施部',             # 发起部门
        'originator_dept_id': '106321170',           # 发起部门
        'status': 'COMPLETED',  # 审批状态，分为NEW（新创建）RUNNING（运行中）TERMINATED（被终止）COMPLETED（完成）
        'tasks': [   # 已审批任务列表，可以通过此列表获取已审批人
            {
                'url': 'aflow.dingtalk.com?procInsId=62da3b8f-114e-4606-96b3-c96bb2349361&taskId=61958382690&businessId=201908142306000412195',
                'create_time': '2019-08-14 23:06:42',
                'userid': '021038163631880229',  # 任务处理人
                'finish_time': '2019-08-14 23:07:16',
                'task_status': 'COMPLETED',  # 任务状态，分为NEW（未启动），RUNNING（处理中），CANCELED（取消），COMPLETED（完成）
                'taskid': '61958382690',
                'task_result': 'AGREE'  # 结果，分为NONE（无），AGREE（同意），REFUSE（拒绝），REDIRECTED（转交
            }, {
                'url': 'aflow.dingtalk.com?procInsId=62da3b8f-114e-4606-96b3-c96bb2349361&taskId=61958382691&businessId=201908142306000412195',
                'create_time': '2019-08-14 23:06:42',
                'userid': 'V00_1400815737560',
                'task_status': 'CANCELED',
                'taskid': '61958382691',
                'task_result': 'NONE'
            }
        ],
        'result': 'agree',  # 审批结果，分为 agree 和 refuse
        'title': 'lallaalsadasdasd提交的外出申请',
        'create_time': '2019-08-14 23:06:42',  # 开始时间。
        'finish_time': '2019-08-14 23:07:16',  # 结束时间
        'business_id': '201908142306000412195',  # 审批实例业务编号
        'operation_records': [  # 操作记录列表
            {
                'userid': '2660205649-53768585',
                'operation_type': 'START_PROCESS_INSTANCE',
                'date': '2019-08-14 23:06:41',
                'operation_result': 'NONE'
            }, {
                'remark': '同意',
                'operation_type': 'EXECUTE_TASK_NORMAL',  # 操作类型，分为EXECUTE_TASK_NORMAL（正常执行任务），EXECUTE_TASK_AGENT（代理人执行任务）
                                                          # ，APPEND_TASK_BEFORE（前加签任务），APPEND_TASK_AFTER（后加签任务），
                                                          # REDIRECT_TASK（转交任务），START_PROCESS_INSTANCE（发起流程实例），
                                                          # TERMINATE_PROCESS_INSTANCE（终止(撤销)流程实例），FINISH_PROCESS_INSTANCE（结束流程实例），
                                                          # ADD_REMARK（添加评论）
                'date': '2019-08-14 23:07:15',
                'userid': '021038163631880229',
                'operation_result': 'AGREE'  # 操作结果，分为AGREE（同意），REFUSE（拒绝）
            }, {
                'remark': '',
                'operation_type': 'NONE',
                'date': '2019-08-14 23:07:16',
                'userid': '2660205649-53768585',
                'operation_result': 'NONE'
            }
        ],
        'form_component_values': [      # 表单详情列表
            {
                'component_type': 'TextField',
                'id': 'TextField-JU44NQ2D',
                'name': '申请人',
                'value': 'lallaalsadasdasd'
            }, {
                'component_type': 'TextField',
                'id': 'TextField-JU44NQ2E',
                'name': '开始时间',
                'value': '2019-07-30 15:06:15'
            }, {
                'component_type': 'TextField',
                'id': 'TextField-JU44NQ2F',
                'name': '结束时间',
                'value': '2019-08-14 15:06:15'
            }, {
                'component_type': 'TextareaField',
                'id': '外出事由',
                'name': '外出事由',
                'value': 'asdasdasdasd'
            }, {
                'component_type': 'DDPhotoField',
                'id': '图片',
                'name': '图片',
                'value': 'null'
            }
        ],

    },
    'request_id': '10ua7vjtrj3l2',
    'errcode': 0
}
