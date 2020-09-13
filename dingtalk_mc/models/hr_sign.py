# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class DingTalkSignList(models.Model):
    _name = 'dingtalk.signs.list'
    _description = "签到记录"
    _rec_name = 'emp_id'

    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id, index=True)
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    checkin_time = fields.Datetime(string=u'签到时间')
    place = fields.Char(string='签到地址')
    detail_place = fields.Char(string='签到详细地址')
    remark = fields.Char(string='签到备注')
    visit_user = fields.Char(string='拜访对象')
    latitude = fields.Char(string="经度信息")
    longitude = fields.Char(string="纬度信息")

    @api.model
    def process_dingtalk_chat(self, user_id, sign_time, company):
        """
        接受来自钉钉回调的处理
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                start_time = int(sign_time) - 1002
                end_time = int(sign_time) + 1002
                client = dt.get_client(self, dt.get_dingtalk_config(self, company))
                try:
                    result = client.post('topapi/checkin/record/get', {
                        'userid_list': user_id,
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
                        domain = [('ding_id', '=', data.get('userid')), ('company_id', '=', company.id)]
                        emp = self.env['hr.employee'].sudo().search(domain, limit=1)
                        self.env['dingtalk.signs.list'].sudo().create({
                            'company_id': company.id,
                            'emp_id': emp.id if emp else False,
                            'checkin_time': dt.timestamp_to_local_date(data.get('checkin_time'), self),
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

