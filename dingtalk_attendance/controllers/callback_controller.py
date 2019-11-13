# -*- coding: utf-8 -*-

from odoo.addons.dingtalk_callback.controllers.callback_controller import DingTalkCallBackManage
from odoo.addons.dingtalk_base.tools import dingtalk_api
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


class DingTalkCallBackManageExt(DingTalkCallBackManage):

    def user_check_in(self, userid, signtime):
        """
        用户签到-事件
        :param userid:
        :param signtime:
        :return:
        """
        start_time = int(signtime) - 1002
        end_time = int(signtime) + 1002
        client = dingtalk_api.get_client()
        url = 'topapi/checkin/record/get'
        try:
            result = client.post(url, {
                'userid_list': userid,
                'start_time': str(start_time),
                'end_time': str(end_time),
                'cursor': 0,
                'size': 100,
            })
        except Exception as e:
            _logger.info(e)
            return
        if result.get('errcode') == 0:
            r_result = result.get('result')
            for data in r_result.get('page_list'):
                emp = request.env['hr.employee'].sudo().search([('ding_id', '=', data.get('userid'))], limit=1)
                request.env['dingtalk.signs.list'].sudo().create({
                    'emp_id': emp.id if emp else False,
                    'checkin_time': dingtalk_api.timestamp_to_local_date(data.get('checkin_time')),
                    'place': data.get('place'),
                    'visit_user': data.get('visit_user'),
                    'detail_place': data.get('detail_place'),
                    'remark': data.get('remark'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                })
        else:
            logging.info(">>>获取用户签到记录失败,原因:{}".format(result.get('errmsg')))
        return True

