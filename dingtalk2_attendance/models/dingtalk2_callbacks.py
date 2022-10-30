# -*- coding: utf-8 -*-
import logging
from odoo import models, api
from odoo.addons.dingtalk2_base.tools import dingtalk2_tools as dt
_logger = logging.getLogger(__name__)


class Dingtalk2Callbacks(models.AbstractModel):
    _inherit = 'dingtalk2.callbacks'

    @api.model
    def deal_dingtalk_msg(self, event_type, encrypt_result, res_company):
        """
        处理回调的消息
        :param event_type     钉钉回调类型
        :param encrypt_result 钉钉回调的消息内容
        :param res_company    回调的公司实例
        """
        if event_type == 'check_in':         # 用户签到事件
            self.get_dingtalk2_attendance_sings(res_company, encrypt_result)
        elif event_type == 'attendance_check_record':   # 用户打卡事件（打卡详情，不是打卡结果）
            pass
        return super(Dingtalk2Callbacks, self).deal_dingtalk_msg(event_type, encrypt_result, res_company)

    @api.model
    def get_dingtalk2_attendance_sings(self, res_company, encrypt_result):
        """
        处理用户签到事件，读取该用户的签到记录
        """
        user_id = encrypt_result.get('StaffId')
        sign_time = encrypt_result.get('TimeStamp')
        employee_id = self.env['hr.employee'].sudo().search([('ding_id', '=', user_id)], limit=1)
        if not employee_id:
            return
        client = dt.get_client(self, dt.get_dingtalk2_config(self, res_company))
        try:
            req_result = client.post('topapi/checkin/record/get', {
                'start_time': sign_time,
                'end_time': sign_time,
                'userid_list': user_id,
                'cursor': 0,
                'size': 100,
            })
            if req_result.get('errcode') == 0:
                result = req_result.get('result')
                for rec in result.get('page_list'):
                    self.env['dingtalk2.attendance.signs'].sudo().create({
                        'company_id': res_company.id,
                        'checkin_time': dt.get_time_stamp(rec.get('checkin_time')),
                        'detail_place': rec.get('detail_place'),
                        'remark': rec.get('remark'),
                        'name': employee_id.id,
                        'place': rec.get('place'),
                        'visit_user': rec.get('visit_user'),
                    })
        except Exception as e:
            raise _logger.info("获取用户签到记录失败：{}".format(str(e)))




