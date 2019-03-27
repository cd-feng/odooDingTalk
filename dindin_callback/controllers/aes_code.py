from Crypto.Cipher import AES
import base64


class AEScoder():

    def __init__(self, encrypt_key):
        self.__encryptKey = encrypt_key
        self.__key = base64.b64decode(self.__encryptKey)

    # AES加密
    def encrypt(self, data):
        BS = 16
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        cipher = AES.new(self.__key, AES.MODE_ECB)
        encrData = cipher.encrypt(pad(data))
        # encrData = base64.b64encode(encrData)
        return encrData

    # AES解密
    def decrypt(self, encrData):
        # encrData = base64.b64decode(encrData)
        # unpad = lambda s: s[0:-s[len(s)-1]]
        unpad = lambda s: s[0:-s[-1]]
        cipher = AES.new(self.__key, AES.MODE_ECB)
        decrData = unpad(cipher.decrypt(encrData))
        return decrData.decode('utf-8')
