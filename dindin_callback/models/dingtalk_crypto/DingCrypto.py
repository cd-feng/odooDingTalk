# -*- coding:utf-8 -*-
import datetime
import random
import time
from io import StringIO
import base64, binascii, hashlib, string, struct
from random import choice

from Crypto.Cipher import AES


class DingCrypto:
    def __init__(self, encodingAesKey, key):
        self.encodingAesKey = encodingAesKey
        self.key = key
        self.aesKey = base64.b64decode(self.encodingAesKey + '=')

    def encrypt(self, content):
        """
        加密
        :param content:
        :return:
        """
        msg_len = self.length(content)
        content = self.generateRandomKey(16) + msg_len + content + self.key
        contentEncode = self.pks7encode(content)
        iv = self.aesKey[:16]
        aesEncode = AES.new(self.aesKey, AES.MODE_CBC, iv)
        aesEncrypt = aesEncode.encrypt(contentEncode)
        return base64.encodestring(aesEncrypt).replace('\n', '')

    def length(self, content):
        """
        将msg_len转为符合要求的四位字节长度
        :param content:
        :return:
        """
        l = len(content)
        return struct.pack('>l', l)

    def pks7encode(self, content):
        """
        安装 PKCS#7 标准填充字符串
        :param text: str
        :return: str
        """
        l = len(content)
        output = StringIO()
        val = 32 - (l % 32)
        for _ in xrange(val):
            output.write('%02x' % val)
        return content + binascii.unhexlify(output.getvalue())

    def pks7decode(self, content):
        nl = len(content)
        val = int(binascii.hexlify(content[-1]), 16)
        if val > 32:
            raise ValueError('Input is not padded or padding is corrupt')

        l = nl - val
        return content[:l]

    # 解密钉钉发送的数据
    def decrypt(self, content):
        """
        解密
        :param content:
        :return:
        """
        # content = base64.decodestring(content)  ##钉钉返回的消息体
        content = base64.b64decode(content)
        iv = self.aesKey[:16]  ##初始向量
        aesDecode = AES.new(self.aesKey, AES.MODE_CBC, iv)
        decodeRes = aesDecode.decrypt(content)[20:].replace(self.key, '')
        ##获取去除初始向量，四位msg长度以及尾部corpid
        return self.pks7decode(decodeRes)

    def generateRandomKey(self, size,
                          chars=string.ascii_letters + string.ascii_lowercase + string.ascii_uppercase + string.digits):
        """
        生成加密所需要的随机字符串
        :param size:
        :param chars:
        :return:
        """
        return ''.join(choice(chars) for i in range(size))

    def generateSignature(self, token, msg_encrypt):
        """
        签名消息
        :param token:
        :param msg_encrypt:
        :return:
        """
        timestamp = str(self.get_timestamp())
        nonce = self.random_alpha()
        signList = ''.join(sorted([nonce, timestamp, token, msg_encrypt]))
        return hashlib.sha1(signList.encode('utf-8')).hexdigest()

    def get_timestamp(self):
        """
        生成现在的Epoch时间
        :return: int
        """
        now = datetime.datetime.now()
        return int(time.mktime(now.timetuple()))

    def random_alpha(self, length=8):
        """
        随机生成指定长度的 Alpha 字符串
        :param length: int
        :return: str
        """
        return ''.join(random.sample(string.ascii_letters + string.digits, length))