# -*- coding: utf-8 -*-

import time
import datetime
import random
import string
alpha = string.ascii_letters + string.digits


def get_timestamp():
    """
    生成现在的Epoch时间
    :return: int
    """
    now = datetime.datetime.now()
    return int(time.mktime(now.timetuple()))


def random_alpha(length=8):
    """
    随机生成指定长度的 Alpha 字符串
    :param length: int
    :return: str
    """
    # with contextlib.closing(StringIO()) as buf:
    #     for _ in range(length):
    #         buf.write(random.choice(alpha))
    #     return buf.read()
    return ''.join(random.sample(string.ascii_letters + string.digits, length))
