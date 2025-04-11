# -*- coding: utf-8 -*-
import requests
import time
import logging
import threading
logger = logging.getLogger(__name__)

DINGTALK_API_BASE_URL = "https://oapi.dingtalk.com"

class DingTalkAPIError(Exception):
    """
    自定义钉钉 API 异常
    """
    def __init__(self, errcode, errmsg, *args):
        super().__init__(f"钉钉API错误: [Code: {errcode}] {errmsg}", *args)
        self.errcode = errcode
        self.errmsg = errmsg

class DingTalkClient:
    """
    钉钉客户端
    """

    def __init__(self, app_key, app_secret):
        """
        初始化客户端。
        :param app_key: 钉钉应用的 AppKey (在开发者后台查看)
        :param app_secret: 钉钉应用的 AppSecret
        """
        if not app_key or not app_secret:
            raise ValueError("App Key 和 App Secret 不能为空")
        self.app_key = app_key
        self.app_secret = app_secret
        self._access_token = None
        self._expires_at = 0
        self._token_lock = threading.Lock()

    def _fetch_access_token(self):
        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        data = {
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if "accessToken" in result:
                self._access_token = result["accessToken"]
                expires_in = result.get("expireIn", 7200)
                self._expires_at = time.time() + expires_in - 60
                return self._access_token
            else:
                self._access_token = None
                self._expires_at = 0
                raise DingTalkAPIError(400, f"获取Token失败: {result}")
        except Exception as e:
            self._access_token = None
            self._expires_at = 0
            raise DingTalkAPIError(errcode=200, errmsg=f"处理Token请求时发生错误: {e}") from e

    def get_access_token(self):
        """
        获取有效的 Access Token。  如果当前 Token 无效或即将过期，会自动获取新的 Token。
        此方法是线程安全的。
        """
        with self._token_lock:
            if self._access_token and time.time() < self._expires_at:
                return self._access_token
            else:
                return self._fetch_access_token()

    def _request(self, method, api_path, params=None, json_data=None, **kwargs):
        """
        内部方法：封装了 API 请求的通用逻辑。
        :param method: HTTP 方法 (GET, POST, etc.)
        :param api_path: API 的路径 (例如 /user/get)
        :param params: URL 查询参数 (字典)
        :param json_data: POST/PUT 请求的 JSON body (字典)
        :param kwargs: 其他传递给 requests.request 的参数 (如 headers, timeout)
        :return: API 响应的 JSON 字典
        :raises: DingTalkAPIError, requests.exceptions.RequestException
        """
        access_token = self.get_access_token()
        url = f"{DINGTALK_API_BASE_URL}{api_path}"
        request_params = params.copy() if params else {}
        request_params['access_token'] = access_token
        headers = kwargs.pop('headers', {})
        if json_data is not None:
            headers.setdefault('Content-Type', 'application/json')
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                params=request_params,
                json=json_data,
                headers=headers,
                timeout=kwargs.get('timeout', 15),
                **kwargs
            )
            response.raise_for_status()
            result = response.json()
            errcode = result.get("errcode")
            if errcode is not None and errcode != 0:
                 errmsg = result.get("errmsg", "钉钉API返回未知业务错误")
                 logger.warning(f"钉钉API调用返回错误: [Code: {errcode}] {errmsg} (URL: {url})")
                 raise DingTalkAPIError(errcode, errmsg)
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求网络错误 ({method} {api_path}): {e}")
            raise DingTalkAPIError(errcode=-100, errmsg=f"钉钉API请求失败: {e}")
        except ValueError as e:
             raise DingTalkAPIError(errcode=-102, errmsg=f"无法解析响应 JSON: {e}")

