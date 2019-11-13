# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class HrDingDingPlanTran(models.TransientModel):
    _name = "hr.dingtalk.plan.tran"
    _description = "排班列表查询"

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=str(fields.datetime.now()))

    def get_plan_lists(self):
        """
        获取企业考勤排班详情
        :return:
        """
        self.ensure_one()
        self.start_pull_plan_lists(self.start_date, self.stop_date)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def start_pull_plan_lists(self, start_date, stop_date):
        """
        拉取排班信息
        :param start_date: string 查询的开始日期
        :param stop_date: string 查询的结束日期
        :return:
        """
        # 删除已存在的排班信息
        self.env['hr.dingtalk.plan'].sudo().search([('plan_check_time', '>=', start_date), ('plan_check_time', '<=', stop_date)]).unlink()
        din_client = dingtalk_api.get_client()
        _logger.info(">>>------开始获取排班信息-----------")
        work_date = start_date
        while work_date <= stop_date:
            offset = 0
            size = 200
            while True:
                result = din_client.attendance.listschedule(work_date, offset=offset, size=size)
                _logger.info(">>>获取排班信息返回结果%s", result)
                if result.get('ding_open_errcode') == 0:
                    res_result = result.get('result')
                    plan_data_list = list()
                    if not res_result['schedules'] or not res_result['schedules']['at_schedule_for_top_vo']:
                        break
                    for schedules in res_result['schedules']['at_schedule_for_top_vo']:
                        plan_data = {
                            'class_setting_id': schedules['class_setting_id'] if 'class_setting_id' in schedules else "",
                            'check_type': schedules['check_type'] if 'check_type' in schedules else "",
                            'plan_id': schedules['plan_id'] if 'plan_id' in schedules else "",
                            'class_id': schedules['class_id'] if 'class_id' in schedules else "",
                        }
                        if 'plan_check_time' in schedules:
                            utc_plan_check_time = datetime.strptime(
                                schedules['plan_check_time'], "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)
                            plan_data.update({'plan_check_time': utc_plan_check_time})
                        simple = self.env['dingtalk.simple.groups'].search(
                            [('group_id', '=', schedules['group_id'])], limit=1)
                        employee = self.env['hr.employee'].search([('ding_id', '=', schedules['userid'])], limit=1)
                        plan_data.update({
                            'group_id': simple.id if simple else False,
                            'user_id': employee.id if employee else False,
                        })
                        plan_data_list.append(plan_data)
                    self.env['hr.dingtalk.plan'].create(plan_data_list)
                    if not res_result['has_more']:
                        break
                    else:
                        offset += size
                else:
                    raise UserError("获取企业考勤排班详情失败: {}".format(result['errmsg']))
            work_date = work_date + timedelta(days=1)
        logging.info(">>>------结束获取排班信息-----------")
        return

    def clear_hr_dingding_plan(self):
        """
        清除已下载的所有钉钉排班记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
            delete from hr_dingding_plan
        """)
