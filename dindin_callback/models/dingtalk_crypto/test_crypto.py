# -*- coding: utf-8 -*-
import json
from .crypto import DingTalkCrypto

# 这个是钉钉官方给的测试数据
# @see https://open-doc.dingtalk.com/doc2/detail.htm?treeId=175&articleId=104945&docType=1#s14
encrypt_text = '1a3NBxmCFwkCJvfoQ7WhJHB+iX3qHPsc9JbaDznE1i03peOk1LaOQoRz3+nlyGNhwmwJ3vDMG' \
               '+OzrHMeiZI7gTRWVdUBmfxjZ8Ej23JVYa9VrYeJ5as7XM/ZpulX8NEQis44w53h1qAgnC3PRzM7Zc' \
               '/D6Ibr0rgUathB6zRHP8PYrfgnNOS9PhSBdHlegK+AGGanfwjXuQ9+0pZcy0w9lQ=='

crypto = DingTalkCrypto(
    '4g5j64qlyl3zvetqxz5jiocdr586fn2zvjpa8zls3ij',
    '123456',
    'suite4xxxxxxxxxxxxxxx'
)

signature = '5a65ceeef9aab2d149439f82dc191dd6c5cbe2c0'
timestamp = '1445827045067'
nonce = 'nEXhMP4r'


class TestCrypto:
    def test_decrypt(self):
        randstr, length, msg, suite_key = crypto.decrypt(encrypt_text)
        msg = json.loads(msg)

        assert msg['EventType'] == 'check_create_suite_url'
        assert msg['Random'] == 'LPIdSnlF'
        assert suite_key == 'suite4xxxxxxxxxxxxxxx'

    def test_encode(self):
        encrypt_msg = crypto.encrypt('hello world')
        randstr, length, msg, suite_key = crypto.decrypt(encrypt_msg)
        assert msg == 'hello world'

    def test_check_signature(self):
        assert crypto.check_signature(encrypt_text, timestamp, nonce, signature)

    def test_sign(self):
        msg = crypto.encrypt('hello world')
        actual_sig, actual_time, actual_nonce = crypto.sign(msg)
        assert True
