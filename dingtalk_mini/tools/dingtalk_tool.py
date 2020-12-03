# -*- coding: utf-8 -*-

import odoo
import logging
import time
from datetime import datetime, timedelta
from odoo import fields
from odoo.exceptions import UserError
from odoo.http import request


_logger = logging.getLogger(__name__)


def get_dingtalk_mini_config(self, agent_id, company):
    """
    获取小程序配置项
    :return:
    """
    config = self.env['dingtalk.mini.config'].sudo().search([('agent_id', '=', agent_id),('company_id', '=', company.id)])
    if not config:
        raise UserError("没有为:(%s)配置钉钉小程序(%s)参数！" % (company.name, agent_id))
    return config


odoo.addons.dingtalk_mc.tools.dingtalk_tool.get_dingtalk_mini_config = get_dingtalk_mini_config

# def get_config_is_delete(self, company):
#     """
#     返回对应公司钉钉配置项中是否"删除基础数据自动同步"字段
#     :return:
#     """
#     config = self.env['dingtalk.mini.config'].sudo().search([('company_id', '=', company.id)])
#     if not config:
#         raise UserError("没有为:(%s)配置钉钉参数！" % company.name)
#     return config.delete_is_sy


# def timestamp_to_local_date(time_num, obj=None):
#     """
#     将13位毫秒时间戳转换为本地日期(+8h)
#     :param time_num:
#     :param obj: object
#     :return: string datetime
#     """
#     if not time_num:
#         return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
#     to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
#     to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
#     to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
#     to_local_datetime = fields.Datetime.context_timestamp(obj, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
#     to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
#     return to_str_datetime


# def get_time_stamp(timeNum):
#     """
#     将13位时间戳转换为时间utc=0
#     :param timeNum:
#     :return: "%Y-%m-%d %H:%M:%S"
#     """
#     timeStamp = float(timeNum / 1000)
#     timeArray = time.gmtime(timeStamp)
#     otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
#     return otherStyleTime


# def datetime_to_stamp(time_num):
#     """
#     将时间转成13位时间戳
#     :param time_num:
#     :return: date_stamp
#     """
#     date_str = fields.Datetime.to_string(time_num)
#     date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
#     date_stamp = date_stamp * 1000
#     return int(date_stamp)


# def utc2local(utc_dtm):
#     """
#     UTC 时间转本地时间（ +8:00 ）
#     :param utc_dtm:
#     :return:
#     """
#     local_tm = datetime.fromtimestamp(0)
#     utc_tm = datetime.utcfromtimestamp(0)
#     offset = local_tm - utc_tm
#     return utc_dtm + offset


# def local2utc(local_dtm):
#     """
#     本地时间转 UTC 时间（ -8:00 ）
#     :param local_dtm:
#     :return:
#     """
#     return datetime.utcfromtimestamp(local_dtm.timestamp())


# def list_cut(mylist, limit):
#     """
#     列表分段
#     :param mylist:列表集
#     :param limit: 子列表元素限制数量
#     :return:
#     """
#     length = len(mylist)
#     cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
#     return cut_list


# def day_cut(begin_time, end_time, days):
#     """
#     日期分段
#     :param begin_date:开始日期
#     :param end_date:结束日期
#     :param days: 最大间隔时间
#     :return:
#     """
#     cut_day = []
#     begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
#     end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
#     delta = timedelta(days=days)
#     t1 = begin_time
#     while t1 <= end_time:
#         if end_time < t1 + delta:
#             t2 = end_time
#         else:
#             t2 = t1 + delta
#         t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
#         t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
#         cut_day.append([t1_str, t2_str])
#         # t1 = t2 + timedelta(seconds=1)
#         t1 = t2 + timedelta(days=1)
#     return cut_day


# def user_info_by_dingtalk_code(self, code, company):
#     """
#     根据扫码或账号密码登录返回的code获取用户信息
#     :param self:
#     :param code: code  账号或扫码登录返回的code
#     :param company: 公司
#     :return:
#     """
#     client = get_client(self, get_dingtalk_mini_config(self, company))
#     config = request.env['dingtalk.mini.config'].sudo().search([('company_id', '=', company.id)], limit=1)
#     login_id = config.login_id
#     login_secret = config.login_secret
#     milli_time = lambda: int(round(time.time() * 1000))
#     timestamp = str(milli_time())
#     signature = hmac.new(login_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
#     signature = quote(base64.b64encode(signature), 'utf-8')
#     url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(signature, timestamp, config.login_id)
#     result = client.post(url, {
#         'tmp_auth_code': code,
#         'signature': signature,
#         'timestamp': timestamp,
#         'accessKey': login_id
#     })
#     return result.user_info