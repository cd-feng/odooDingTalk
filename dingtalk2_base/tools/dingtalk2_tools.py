# -*- coding: utf-8 -*-
import random
import string
import logging
import time
from datetime import datetime, timedelta
from odoo import SUPERUSER_ID, fields
try:
    from dingtalk.client import AppKeyClient
    from dingtalk.storage.memorystorage import MemoryStorage
except ImportError:
    raise ImportError('该模块需要dingtalk-sdk才能正常使用，请安装dingtalk-sdk到系统环境中（sudo pip3 install dingtalk-sdk）')
mem_storage = MemoryStorage()
_logger = logging.getLogger(__name__)


def get_client(self, config):
    """
    得到客户端
    :param self
    :param config:
    :return:
    """
    corp_id = config.corp_id.replace(' ', '')
    app_key = config.app_key.replace(' ', '')
    app_secret = config.app_secret.replace(' ', '')
    return AppKeyClient(corp_id, app_key, app_secret, storage=mem_storage)


def get_dingtalk2_config(self, company):
    """
    获取配置项
    :return:
    """
    return self.env['dingtalk2.config'].with_user(SUPERUSER_ID).search([('company_id', '=', company.id)])


def get_random_character(size):
    """
    返回指定长度的随机字符串
    :param size 指定的长度
    :return str
    """
    return ''.join(random.sample(string.ascii_letters + string.digits, size))


def timestamp_to_local_date(self, time_num):
    """
    将13位毫秒时间戳转换为本地日期(+8h)
    :param time_num:
    :param obj: object
    :return: string datetime
    """
    if not time_num:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    to_second_timestamp = float(time_num / 1000)
    to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    to_datetime = fields.Datetime.from_string(to_str_datetime) + timedelta(hours=8)  # 将字符串转成datetime对象
    to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return to_str_datetime


def get_time_stamp(time_num):
    """
    将13位时间戳转换为时间utc=0
    :param time_num:
    :return: "%Y-%m-%d %H:%M:%S"
    """
    time_array = time.gmtime(float(time_num / 1000))
    return time.strftime("%Y-%m-%d %H:%M:%S", time_array)


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
    :param begin_time:开始日期
    :param end_time:结束日期
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
        t1 = t2 + timedelta(days=1)
    return cut_day


def signs_day_cut(begin_time, end_time, days):
    """
    日期分段
    :param begin_time:开始日期
    :param end_time:结束日期
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
        t1 = t2 + timedelta(days=1)
    return cut_day


def get_time_stamp13(begin_time):
    """
    获取指定datetime时间的13位时间戳
    """
    date_stamp = str(int(time.mktime(begin_time.timetuple())))
    data_microsecond = str("%06d" % begin_time.microsecond)[0:3]
    date_stamp = date_stamp + data_microsecond
    return int(date_stamp)
