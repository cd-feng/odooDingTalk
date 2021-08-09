# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, SUPERUSER_ID, api
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)

# 员工回调事件
EmployeeEvents = ['user_add_org', 'user_modify_org', 'user_leave_org']
# 部门回调事件
DepartmentEvents = ['org_dept_create', 'org_dept_modify', 'org_dept_remove']
# 审批回调事件
ApprovalEvents = ['bpms_task_change', 'bpms_instance_change']
# 签到事件
CheckInEvents = ['check_in']
# 考勤事件
AttendanceEvents = ['attendance_check_record', 'attendance_schedule_change', 'attendance_overtime_duration']
# 会议室事件
MeetingroomEvents = ['meetingroom_book', 'meetingroom_room_info']


class DingtalkProcessingCallbacks(models.AbstractModel):
    _name = 'dingtalk.processing.callbacks'
    _description = "处理钉钉回调"

    @api.model
    def process_dingtalk_chat(self, encrypt_result, company_id):
        """
        处理钉钉回调的结果
        :param encrypt_result: 解密后的消息
        :param company_id: 当前公司id
        :return:
        """
        _logger.info(">回调消息内容：{}".format(encrypt_result))
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                company_id = self.env['res.company'].sudo().search([('id', '=', company_id)])
                try:
                    result_index = encrypt_result.index('}')
                    new_encrypt_result = encrypt_result[0:result_index + 1]
                    encrypt_result = json.loads(new_encrypt_result.encode('utf-8'))  # 消息内容
                except Exception:
                    try:
                        encrypt_result = json.loads(encrypt_result.encode('utf-8'))
                    except Exception:
                        return
                event_type = encrypt_result.get('EventType')  # 回调的事件
                # 创建日志
                try:
                    self.env['dingtalk.callback.log'].create_dingtalk_log(company_id, encrypt_result, event_type)
                except Exception as e:
                    _logger.info(">: 创建钉钉回调日志失败，原因为： {}".format(str(e)))
                if event_type in EmployeeEvents:
                    # 员工回调事件
                    return self.dingtalk_employee_callback(encrypt_result, company_id)
                elif event_type in DepartmentEvents:
                    # 部门回调事件
                    return self.dingtalk_department_callback(encrypt_result, company_id)
                elif event_type in ApprovalEvents:
                    # 钉钉审批事件
                    return self.dingtalk_approval_callback(encrypt_result, company_id)
                elif event_type in AttendanceEvents or event_type in CheckInEvents:
                    # 考勤或签到事件时
                    return self.dingtalk_attendance_callback(encrypt_result, company_id)
                else:
                    # 其他事件不做处理
                    pass

    def dingtalk_employee_callback(self, encrypt_result, company_id):
        """
        处理钉钉员工回调事件
        :param encrypt_result:
        :param company_id:
        :return:
        """
        event_type = encrypt_result.get('EventType')  # 消息类型
        user_ids = encrypt_result.get('UserId')       # 发生用户的ids
        if event_type == 'user_leave_org':            # 用户离职
            for user_id in user_ids:
                domain = [('ding_id', '=', user_id), ('company_id', '=', company_id.id)]
                employee = self.env['hr.employee'].sudo().search(domain, limit=1)
                if employee:
                    employee.write({'work_status': '3', 'active': False})
        elif event_type == 'user_add_org':
            # 新增员工
            self.env['hr.employee'].sudo().add_dingtalk_employee(user_ids, company_id)
        else:
            # 用户变更
            self.env['hr.employee'].sudo().modify_dingtalk_employee(user_ids, company_id)

    def dingtalk_department_callback(self, encrypt_result, company_id):
        """
        处理部门回调事件
        :param encrypt_result:
        :param company_id:
        :return:
        """
        event_type = encrypt_result.get('EventType')  # 消息类型
        dept_ids = encrypt_result.get('DeptId')
        if event_type == 'org_dept_remove':
            departments = self.env['hr.department'].sudo().search(
                [('ding_id', 'in', dept_ids), ('company_id', '=', company_id.id)])
            if departments:
                departments.write({'active': False})
        else:
            # 部门增加和变更时获取该部门详情
            self.env['hr.department'].sudo().get_department_info(dept_ids, company_id)

    def dingtalk_approval_callback(self, encrypt_result, company_id):
        """
        处理钉钉审批回调事件
        :param encrypt_result:
        :param company_id:
        :return:
        """
        pass

    def dingtalk_attendance_callback(self, encrypt_result, company_id):
        """
        考勤和签到事件
        :return:
        """
        pass


