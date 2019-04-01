# -*- coding: utf-8 -*-
import requests, json, time


class DingTalk:
    def __init__(self, app_key=None, app_secret=None, sns_app_id=None, sns_app_secret=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.sns_app_id = sns_app_id
        self.sns_app_secret = sns_app_secret

    def send_request(self, method, request_url, data, retry=True, retry_count=0, retry_interval=3):
        """
        发送HTTP请求
        """
        headers = {
            'Content-Type': 'application/json;charset=utf-8'
        }
        if method == 'GET':
            res = requests.get(request_url, params=data, headers=headers, verify=False)
        if method == 'POST':
            res = requests.post(request_url, data=json.dumps(data), headers=headers, verify=False)
        result = res.json()
        if result.get('errcode') != 0:
            if retry:
                if retry_count <= 5:
                    # 接口访问出错时重试
                    time.sleep(retry_interval)
                    return self.send_request(method, request_url, data, retry_count=retry_count + 1)
                else:
                    raise Exception('（钉钉接口错误）' + result.get('errmsg') + ' | （接口地址）' + request_url)
            else:
                raise Exception('（钉钉接口错误）' + result.get('errmsg') + ' | （接口地址）' + request_url)
        else:
            return result

    def get_access_token_data(self):
        """
        获取AccessToken数据
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/gettoken'
        params = {
            'appkey': self.app_key,
            'appsecret': self.app_secret
        }
        result = self.send_request(method, url, params)
        return result

    def get_access_token(self):
        """
        获取AccessToken
        """
        return self.get_access_token_data().get('access_token')

    def get_access_token_param(self):
        """
        获取AccessToken Get参数
        """
        return '?access_token=' + self.get_access_token_data().get('access_token')

    def get_user_info_by_id(self, user_id):
        """
        通过UserId获取用户基本信息
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/user/get'
        params = {
            'access_token': self.get_access_token(),
            'userid': user_id
        }
        result = self.send_request(method, url, params)
        return result

    def get_user_detail_by_ids(self, user_ids):
        """
        通过一组UserId获取一组用户的详细信息
        """
        method = 'POST'
        url = 'https://oapi.dingtalk.com/topapi/smartwork/hrm/employee/list' + self.get_access_token_param()
        data = {
            'userid_list': user_ids,
            'field_filter_list': "sys00-name,sys00-email,sys00-dept,sys00-mainDept,sys00-mobile",
        }
        result = self.send_request(method, url, data)
        return result

    def get_user_info_by_auth_code(self, auth_code):
        """
        通过AuthCode获取用户基本信息
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/user/getuserinfo'
        params = {
            'access_token': self.get_access_token(),
            'code': auth_code
        }
        result = self.send_request(method, url, params)
        return result

    def get_sns_access_token_data(self):
        """
        获取SNSAccessToken
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/sns/gettoken'
        params = {
            'appid': self.sns_app_id,
            'appsecret': self.sns_app_secret
        }
        result = self.send_request(method, url, params)
        return result

    def get_sns_access_token(self):
        return self.get_sns_access_token_data().get('access_token')

    def get_sns_access_token_param(self):
        return '?access_token=' + self.get_sns_access_token()

    def get_sns_persistent_code(self, code):
        """
        获取SNSPersistentCode
        """
        method = 'POST'
        url = 'https://oapi.dingtalk.com/sns/get_persistent_code' + self.get_sns_access_token_param()
        data = {
            'tmp_auth_code': code
        }
        result = self.send_request(method, url, data)
        return result

    def get_sns_token(self, openid, persistent_code):
        """
        获取SNSToken
        """
        method = 'POST'
        url = 'https://oapi.dingtalk.com/sns/get_sns_token' + self.get_sns_access_token_param()
        data = {
            'openid': openid,
            'persistent_code': persistent_code
        }
        result = self.send_request(method, url, data)
        return result

    def get_sns_user_info(self, sns_token):
        """
        获取SNSUserInfo
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/sns/getuserinfo'
        params = {
            'sns_token': sns_token,
        }
        result = self.send_request(method, url, params)
        return result

    def get_user_id_by_unionid(self, unionid):
        """
        通过UnionId获取UserId
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/user/getUseridByUnionid'
        params = {
            'access_token': self.get_access_token(),
            'unionid': unionid
        }
        result = self.send_request(method, url, params)
        return result

    def get_user_id_list_by_paging(self, offset):
        """
        分页获取在职用户Id列表
        """
        method = 'POST'
        url = 'https://oapi.dingtalk.com/topapi/smartwork/hrm/employee/queryonjob' + self.get_access_token_param()
        data = {
            'status_list': '2,3',
            'offset': offset,
            'size': 20
        }
        result = self.send_request(method, url, data)
        return result

    def get_user_id_list(self):
        """
        获取所有在职用户Id
        """
        offset = 0
        userid_list = []
        # 循环分页获取所有UserId
        while True:
            result = self.get_user_id_list_by_paging(offset).get('result')
            userid_list.extend(result.get('data_list'))
            # 检测分页是否结束
            if result.get('next_cursor') != None:
                offset = result.get('next_cursor')
            else:
                break
        return userid_list

    def get_dimission_user_id_list_by_paging(self, offset, retry=False):
        """
        分页获取离职用户Id列表
        """
        method = 'POST'
        url = 'https://oapi.dingtalk.com/topapi/smartwork/hrm/employee/querydimission' + self.get_access_token_param()
        data = {
            'offset': offset,
            'size': 20
        }
        result = self.send_request(method, url, data)
        return result

    def get_dimission_user_id_list(self):
        """
        获取所有离职用户Id
        """
        offset = 0
        userid_list = []
        # 循环分页获取所有UserId
        while True:
            result = self.get_dimission_user_id_list_by_paging(offset).get('result')
            userid_list.extend(result.get('data_list'))
            # 检测分页是否结束
            if result.get('next_cursor') != None:
                offset = result.get('next_cursor')
            else:
                break
        return userid_list

    def callback_api_register(self, call_back_tag, token, aes_key, call_back_url):
        """
        业务回调接口 注册接口
        """
        method = 'POST'
        url = 'https://oapi.dingtalk.com/call_back/register_call_back' + self.get_access_token_param()
        data = {
            'call_back_tag': call_back_tag,
            'token': token,
            'aes_key': aes_key,
            'url': call_back_url
        }
        result = self.send_request(method, url, data)
        return result

    def get_departments(self, id, fetch_child=False):
        """
        根据Id获取部门列表
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/department/list'
        params = {
            'access_token': self.get_access_token(),
            'id': id,
            'fetch_child': fetch_child
        }
        result = self.send_request(method, url, params)
        return result

    def get_department_info(self, id):
        """
        根据Id获取部门信息
        """
        method = 'GET'
        url = 'https://oapi.dingtalk.com/department/get'
        params = {
            'access_token': self.get_access_token(),
            'id': id
        }
        result = self.send_request(method, url, params)
        return result
