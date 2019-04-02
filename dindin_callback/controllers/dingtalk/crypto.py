# -*- coding:utf-8 -*-
import io, base64, binascii, hashlib, string, struct
from random import choice
from Crypto.Cipher import AES


class DingTalkCrypto:
    def __init__(self, encodingAesKey, key):
        self.encodingAesKey = encodingAesKey
        self.key = key
        self.aesKey = base64.b64decode(self.encodingAesKey + '=')

    def encrypt(self, content):
        """
        加密
        """
        msg_len = self.length(content)
        content = self.generateRandomKey(16) + msg_len.decode() + content + self.key
        contentEncode = self.pks7encode(content)
        iv = self.aesKey[:16]
        aesEncode = AES.new(self.aesKey, AES.MODE_CBC, iv)
        aesEncrypt = aesEncode.encrypt(contentEncode)
        return base64.b64encode(aesEncrypt).decode().replace('\n', '')

    def length(self, content):
        """
        将msg_len转为符合要求的四位字节长度
        """
        l = len(content)
        return struct.pack('>l', l)

    def pks7encode(self, content):
        """
        安装 PKCS#7 标准填充字符串
        """
        l = len(content)
        output = io.StringIO()
        val = 32 - (l % 32)
        for _ in xrange(val):
            output.write('%02x' % val)
        return bytes(content, 'utf-8') + binascii.unhexlify(output.getvalue())

    def pks7decode(self, content):
        nl = len(content)
        val = int(binascii.hexlify(content[-1].encode()), 16)
        if val > 32:
            raise ValueError('Input is not padded or padding is corrupt')
        l = nl - val
        return content[:l]

    def decrypt(self, content):
        """
        解密数据
        """
        # 钉钉返回的消息体
        content = base64.b64decode(content)
        iv = self.aesKey[:16]  # 初始向量
        aesDecode = AES.new(self.aesKey, AES.MODE_CBC, iv)
        decodeRes = aesDecode.decrypt(content)[20:].decode().replace(self.key, '')
        # 获取去除初始向量，四位msg长度以及尾部corpid
        return self.pks7decode(decodeRes)

    def generateRandomKey(self, size,
                          chars=string.ascii_letters + string.ascii_lowercase + string.ascii_uppercase + string.digits):
        """
        生成加密所需要的随机字符串
        """
        return ''.join(choice(chars) for i in range(size))

    def generateSignature(self, nonce, timestamp, token, msg_encrypt):
        """
        生成签名
        """
        signList = ''.join(sorted([nonce, timestamp, token, msg_encrypt])).encode()
        return hashlib.sha1(signList).hexdigest()
