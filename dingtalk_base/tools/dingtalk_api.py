# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta, timezone
import requests
from odoo import fields, _
from urllib.parse import quote
from odoo.exceptions import ValidationError

try:
    from dingtalk.client import AppKeyClient
    from dingtalk.storage.memorystorage import MemoryStorage
    from odoo.http import request
except ImportError as e:
    logging.info(_("-------Import Error-----------------------"))
    logging.info(_("引入钉钉三方SDK出错！请检查是否正确安装SDK！！！"))
    logging.info(_("-------Import Error-----------------------"))

mem_storage = MemoryStorage()
_logger = logging.getLogger(__name__)


def get_client(obj):
    """
    得到客户端
    :return: client
    """
    dt_corp_id = obj.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    app_key, app_secret = _get_key_and_secrect(obj)
    return AppKeyClient(dt_corp_id, app_key, app_secret, storage=mem_storage)


def _get_key_and_secrect(self):
    """
    获取配置项中钉钉key和app_secret
    :return:
    """
    app_key = self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_key')
    app_secret = self.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_secret')
    if app_key and app_secret:
        return app_key.replace(' ', ''), app_secret.replace(' ', '')
    return '0000', '0000'


def get_delete_is_synchronous():
    """
    判读是否删除odoo员工、部门、联系人时同时删除钉钉上的数据
    :return:
    """
    return request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_delete_is_sy')


def get_login_id():
    """
    返回登录id
    :return: login_id
    """
    login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    if login_id:
        return login_id.replace(' ', '')
    return '0000'


def get_login_id_and_key():
    """
    :return: login_id
    """
    login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    dt_login_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_secret')
    if login_id and dt_login_secret:
        return login_id.replace(' ', ''), dt_login_secret.replace(' ', '')
    return '0000', '0000'


def get_dt_corp_id():
    """
    :return: dt_corp_id
    """
    dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    if dt_corp_id:
        return dt_corp_id.replace(' ', '')
    return '0000'


def timestamp_to_utc_date(timeNum):
    """
    将13位时间戳转换为时间utc=0
    :param timeNum:
    :return:
    """
    timeStamp = float(timeNum / 1000)
    timeArray = time.gmtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


def timestamp_to_local_date(self, time_num):
    """
    将13位毫秒时间戳转换为本地日期(+8h)
    :param time_num:
    :return: string datetime
    """
    to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
    to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return to_str_datetime


def datetime_to_stamp(time_num):
    """
    将时间转成13位时间戳
    :param time_num:
    :return: date_stamp
    """
    date_str = fields.Datetime.to_string(time_num)
    date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    date_stamp = date_stamp * 1000
    return int(date_stamp)


def datetime_to_local_stamp(self, date_time):
    """
    将utc=0的时间转成13位时间戳(本地时间戳：+8H)
    :param time_num:
    :return: date_stamp
    """
    to_datetime = fields.Datetime.from_string(date_time)
    to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)
    date_str = fields.Datetime.to_string(to_local_datetime)
    date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    date_stamp = date_stamp * 1000
    return int(date_stamp)


def datetime_local_data(date_time, is_date=None):
    """
    将时间戳转为+8小时的日期
    :param date_time: 毫秒级时间戳(int)
    :param is_date:  是否返回日期格式（%Y-%m-%d）
    :return: data_str 默认返回格式（%Y-%m-%d %H:%M:%S） 当re_type为真时返回格式（%Y-%m-%d）
    """
    dt = datetime.fromtimestamp(float(date_time) / 10 ** (len(str(date_time)) - 10), timezone(timedelta(hours=8)))
    return dt.strftime('%Y-%m-%d') if is_date else dt.strftime('%Y-%m-%d %H:%M:%S')


def get_user_info_by_code(code):
    """
    根据扫码或账号密码登录返回的code获取用户信息
    :param code: code  账号或扫码登录返回的code
    :return:
    """
    login_id, login_secret = get_login_id_and_key()
    milli_time = lambda: int(round(time.time() * 1000))
    timestamp = str(milli_time())
    signature = hmac.new(login_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
    signature = quote(base64.b64encode(signature), 'utf-8')
    url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(signature, timestamp, login_id)
    result = get_client(request).post(url, {
        'tmp_auth_code': code,
        'signature': signature,
        'timestamp': timestamp,
        'accessKey': login_id
    })
    return result


def list_cut(mylist, limit):
    """
    列表分段
    :param mylist:列表集
    :param limit: 子列表元素限制数量
    :return:
    """
    length = len(mylist)
    cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
    return cut_list


def day_cut(begin_time, end_time, days):
    """
    日期分段
    :param begin_date:开始日期
    :param end_date:结束日期
    :param days: 最大间隔时间
    :return:
    """
    cut_day = []
    begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
    end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
    delta = timedelta(days=days)
    t1 = begin_time
    while t1 <= end_time:
        if end_time < t1 + delta:
            t2 = end_time
        else:
            t2 = t1 + delta
        t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
        t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
        cut_day.append([t1_str, t2_str])
        t1 = t2 + timedelta(seconds=1)
    return cut_day


def setup_approval_state_fields(self):
    """
    安装钉钉审批字段
    :param self:
    :return:
    """
    def add(name, field):
        if name not in self._fields:
            self._add_field(name, field)
    self._cr.execute("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")
    table = self._cr.fetchall()
    if table[0][0] > 0:
        self._cr.execute(
            """SELECT im.model 
                FROM dingtalk_approval_control dac 
                JOIN ir_model im 
                     ON dac.oa_model_id = im.id 
                WHERE im.model = '%s'
                """ % self._name)
        res = self._cr.fetchall()
        if len(res) != 0:
            add('dd_doc_state', fields.Char(string=u'审批描述'))
            add('dd_approval_state', fields.Selection(string=u'审批状态', selection=[('draft', '草稿'), ('approval', '审批中'), ('stop', '审批结束')], default='draft'))
            add('dd_approval_result', fields.Selection(string=u'审批结果', selection=[('load', '等待'), ('agree', '同意'), ('refuse', '拒绝'), ('redirect', '转交')],
                                                       default='load'))
            add('dd_process_instance', fields.Char(string='钉钉审批实例id'))
    return True


def dingtalk_approval_write(self, vals):
    """不允许单据修改"""
    res_state_obj = self.env.get('dingtalk.approval.control')
    if res_state_obj is None:
        return
    # 关注与取消关注处理
    if len(vals.keys()) == 1 and list(vals.keys())[0] == 'message_follower_ids':
        return
    for res in self:
        model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not flows:
            continue
        if res.dd_approval_state == 'approval':
            # 审批中
            raise ValidationError(u'注意：单据审批中，不允许进行修改。 *_*!!')
        elif res.dd_approval_state == 'stop':
            # 审批完成
            if flows[0].ftype == 'oa':
                raise ValidationError(u'注意：单据已审批完成，不允许进行修改。 *_*!!')
    return True


def dingtalk_approval_unlink(self):
    """非草稿单据不允许删除"""
    res_state_obj = self.env.get('dingtalk.approval.control')
    if res_state_obj is None:
        return
    for res in self:
        model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not flows:
            continue
        if res.dd_approval_state != 'draft':
            raise ValidationError(u'注意：非草稿单据不允许删除。 *_*!!')
    return True
