# -*- coding: utf-8 -*-
from .dingtalk_client import DingTalkClient


class DingTalkHr(DingTalkClient):

    def __init__(self, app_key, app_secret):
        super().__init__(app_key, app_secret)

    def get_department_list(self, dept_id=None, language='zh_CN'):
        """
        示例：获取部门列表 (旧版接口 /department/list)
        :param dept_id: 父部门ID，根部门传 '1' 或 None (具体看接口要求)
        :param language: 通讯录语言 (zh_CN 或 en_US)
        :return: 部门列表信息
        """
        api_path = "/department/list"  # 注意：这是旧版API
        params = {'lang': language}
        if dept_id:
            params['id'] = dept_id
        return self._request("GET", api_path, params=params)

    def get_user_list(self, dept_id=1):
        """
        示例：获取部门用户详情 (/topapi/v2/user/list)
        :return: 部门列表信息
        """
        user_list = []
        api_path = "/topapi/v2/user/list"
        cursor = 0
        while True:
            params = {'dept_id': dept_id, 'cursor': cursor, 'size': 100}
            data = self._request("POST", api_path, params=params)
            result = data.get("result", {})
            user_list.extend(result.get('list', []))
            if not result.get('has_more', False):
                break
            cursor = result.get('next_cursor')
        return user_list