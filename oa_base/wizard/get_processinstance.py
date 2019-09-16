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

import psycopg2

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
            if result.get('errcode') != 0:
                raise UserError(result.get('errmsg'))
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
            logging.info(">>>获取实例详情返回结果%s", result)
            if result['errcode'] == 0:
                process_instance = result['process_instance']
                # get发起人和发起部门
                emp_id, dept_id = self._get_originator_user_and_dept(process_instance['originator_userid'], process_instance['originator_dept_id'])
                model_data = {
                    'originator_user_id': emp_id,   # 发起人
                    'originator_dept_id': dept_id,  # 发起部门
                    'oa_result': process_instance['result'],  # 审批结果
                    'title': process_instance['title'],  # 标题
                    'create_date': process_instance['create_time'],  # 创建时间
                    'write_date': process_instance['finish_time'] if 'finish_time' in process_instance else False,  # 修改/结束时间
                    'business_id': process_instance['business_id'],  # 审批实例业务编号
                    'process_instance_id': process_instance['business_id'],  # 钉钉审批实例id
                }
                # 审批状态
                status = process_instance['status']
                if status == 'NEW':
                    model_data.update({'oa_state': '00'})
                elif status == 'RUNNING':
                    model_data.update({'oa_state': '01'})
                else:
                    model_data.update({'oa_state': '02'})
                # 表单字段详情
                field_dict = self._get_model_filed(odoo_model)
                for form_value in process_instance['form_component_values']:
                    if 'name' in form_value:
                        o_field = field_dict.get(form_value['name'])  # 获取odoo字段
                        if not o_field and form_value['component_type'] != 'DDPhotoField':
                            raise UserError("钉钉字段名 '%s' 与系统字段名不一致，无法同步！" % form_value['name'])
                        # 过滤明细字段和图片附件字段
                        if form_value['component_type'] != 'TableField' and form_value['component_type'] != 'DDPhotoField':
                            if o_field.ttype == 'many2one':    # many2one字段类型
                                domain = [('name', '=', form_value['value'])]
                                many_model = self.env[o_field.relation].sudo().search(domain, limit=1)  # 只支持查询name字段
                                model_data.update({o_field.sudo().name: many_model.id if many_model else False})
                            else:
                                model_data.update({o_field.name: form_value['value']})
                        elif form_value['component_type'] == 'TableField':   # 处理列表
                            # print(form_value)
                            # print(form_value['name'])
                            # print(o_field)
                            line_field_dict = self._get_model_filed(o_field.relation)
                            values = json.loads(form_value['value'])
                            line_list = list()
                            for value in values:
                                line_data = dict()
                                for row_value in value['rowValue']:
                                    line_field = line_field_dict.get(row_value['label'])  # 获取odoo字段
                                    if not line_field:
                                        raise UserError("表单列表明细中字段名 '%s' 与系统字段名不一致，无法同步！" % row_value['label'])
                                    if line_field.ttype == 'many2one':  # many2one字段类型
                                        domain = [('name', '=', row_value['value'])]
                                        many_model = self.env[line_field.relation].sudo().search(domain, limit=1)
                                        line_data.update({line_field.sudo().name: many_model.id if many_model else False})
                                    else:
                                        line_data.update({line_field.name: row_value['value']})
                                line_list.append((0, 0, line_data))
                            model_data.update({o_field.name: line_list})
                try:
                    model_form = self.env[odoo_model.model].sudo().create(model_data)
                except Exception as e:
                    logging.info(str(e))
                    logging.info("字段值不正确导致创建失败，系统将略过...")
                    continue
                # 将审批记录通过消息记录到单据中
                ORESULT = {'AGREE': '同意', 'REFUSE': '拒绝', 'NONE': '无'}
                for records in process_instance['operation_records']:
                    bodys = "操作记录，任务时间：'%s'" % records.get('date')
                    emp = self.env['hr.employee'].sudo().search([('ding_id', '=', records.get('userid'))])
                    bodys = bodys + "， 处理人：'%s'" % emp.name if emp else "无 "
                    bodys = bodys + "，处理结果：'%s'" % ORESULT.get(records.get('operation_result'))
                    bodys = bodys + "，消息：'%s'" % records.get('remark')
                    model_form.sudo().message_post(body=bodys, message_type='notification')
                # 记录已审批任务消息
                TASKRESULT = {'NONE': '无', 'AGREE': '同意', 'REFUSE': '拒绝', 'REDIRECTED': '转交'}
                for task in process_instance['tasks']:
                    emp = self.env['hr.employee'].sudo().search([('ding_id', '=', task.get('userid'))])
                    bodys = "已审批任务，时间：%s，" % task.get('create_time')
                    bodys = bodys + "处理人：%s，" % emp.name if emp else "无"
                    bodys = bodys + "处理结果：%s，" % TASKRESULT.get(task.get('task_result'))
                    model_form.sudo().message_post(body=bodys, message_type='notification')
            else:
                raise UserError(result['errmsg'])
        return True

    @api.model
    def _get_originator_user_and_dept(self, user_id, dept_id):
        """
        返回员工id和部门id
        :param user_id:
        :param dept_id:
        :return:
        """
        emp = self.env['hr.employee'].sudo().search([('ding_id', '=', user_id)], limit=1)
        dept = self.env['hr.department'].sudo().search([('ding_id', '=', dept_id)], limit=1)
        if not emp:
            raise UserError("员工不存在，请先同步员工信息！")
        if not dept:
            raise UserError("部门不存在，请先同步部门信息！")
        return emp.id, dept.id

    @api.model
    def _get_model_filed(self, model):
        """
        返回该模型的标签和字段名dict
        :param model:
        :return:
        """
        field_dict = dict()
        if isinstance(model, str):
            model = self.env['ir.model'].sudo().search([('model', '=', model)], limit=1)
        for field_id in model.field_id:
            field_dict.update({field_id.field_description: field_id})
        return field_dict
