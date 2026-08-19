"""
HTTP 客户端封装

提供统一的 HTTP 请求发送能力，包含：
- Session 管理（连接池复用）
- 自动重试机制（指数退避）
- 超时控制
- 请求/响应日志
- Allure 请求响应详情记录
"""
import time
import json as json_module
import requests
import allure
from requests.exceptions import RequestException, Timeout, ConnectionError as ConnError

from src.core.logger import logger
from src.core.config_manager import config


class HttpClient:
    """
    HTTP 客户端

    封装 requests.Session，提供重试、超时、日志、Allure 附件等功能。
    """

    def __init__(self, base_url: str = None, timeout: int = None, retry_count: int = None):
        """
        初始化 HTTP 客户端。

        Args:
            base_url: 基础URL，默认从配置读取
            timeout: 超时时间（秒），默认从配置读取
            retry_count: 重试次数，默认从配置读取
        """
        self.base_url = base_url or config.base_url
        self.timeout = timeout or config.http_timeout
        self.retry_count = retry_count if retry_count is not None else config.http_retry
        self.session = requests.Session()
        self._access_token = None
        # 存储最后一次请求/响应上下文，供断言失败截图工具读取
        self.last_request = None   # {"method":..., "url":..., "params":..., "body":..., "headers":...}
        self.last_response = None  # requests.Response 对象
        logger.info(f"HttpClient 初始化完成 | base_url={self.base_url} | timeout={self.timeout} | retry={self.retry_count}")

    def set_token(self, token: str):
        """设置认证Token，后续请求自动携带。"""
        self._access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("已设置认证 Token")

    @property
    def token(self):
        """返回当前Token。"""
        return self._access_token

    def _build_url(self, endpoint: str) -> str:
        """拼接完整URL。"""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    def _build_headers(self, headers: dict = None) -> dict:
        """构建请求头。"""
        default_headers = {"Content-Type": "application/json"}
        if self._access_token:
            default_headers["Authorization"] = f"Bearer {self._access_token}"
        if headers:
            default_headers.update(headers)
        return default_headers

    def request(self, method: str, endpoint: str, params=None, json=None,
                data=None, headers=None, **kwargs):
        """
        发送 HTTP 请求（带重试机制）。

        Args:
            method: HTTP方法 (GET/POST/PUT/PATCH/DELETE)
            endpoint: API端点路径
            params: 查询参数
            json: JSON请求体
            data: 表单请求体
            headers: 额外请求头
            **kwargs: 其他requests参数

        Returns:
            requests.Response: 响应对象

        Raises:
            RequestException: 所有重试失败后抛出
        """
        url = self._build_url(endpoint)
        req_headers = self._build_headers(headers)
        method = method.upper()

        # 记录当前请求上下文（供截图工具读取）
        self.last_request = {
            "method": method,
            "url": url,
            "params": params,
            "body": json,
            "headers": req_headers,
        }

        last_exception = None
        for attempt in range(1, self.retry_count + 1):
            try:
                logger.info(f"[{method}] {url} | attempt={attempt}/{self.retry_count}")
                if params:
                    logger.debug(f"请求参数: {params}")
                if json:
                    logger.debug(f"请求体: {json}")

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    headers=req_headers,
                    timeout=self.timeout,
                    **kwargs,
                )

                logger.info(f"响应状态码: {response.status_code} | 耗时: {response.elapsed.total_seconds():.3f}s")

                # 存储最后一次响应对象（供截图工具读取）
                self.last_response = response

                # Allure 记录请求和响应
                self._attach_allure(method, url, response, params, json, req_headers)

                return response

            except Timeout:
                last_exception = Timeout(f"请求超时: {url}")
                logger.warning(f"请求超时 | attempt={attempt} | url={url}")
            except ConnError:
                last_exception = ConnError(f"连接失败: {url}")
                logger.warning(f"连接失败 | attempt={attempt} | url={url}")
            except RequestException as e:
                last_exception = e
                logger.warning(f"请求异常 | attempt={attempt} | error={e}")

            if attempt < self.retry_count:
                wait_time = 2 ** (attempt - 1)
                logger.info(f"等待 {wait_time}s 后重试...")
                time.sleep(wait_time)

        logger.error(f"请求最终失败 | url={url} | 重试次数={self.retry_count}")
        raise last_exception

    def get(self, endpoint, params=None, **kwargs):
        """发送 GET 请求。"""
        return self.request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint, json=None, **kwargs):
        """发送 POST 请求。"""
        return self.request("POST", endpoint, json=json, **kwargs)

    def put(self, endpoint, json=None, **kwargs):
        """发送 PUT 请求。"""
        return self.request("PUT", endpoint, json=json, **kwargs)

    def patch(self, endpoint, json=None, **kwargs):
        """发送 PATCH 请求。"""
        return self.request("PATCH", endpoint, json=json, **kwargs)

    def delete(self, endpoint, **kwargs):
        """发送 DELETE 请求。"""
        return self.request("DELETE", endpoint, **kwargs)

    def _attach_allure(self, method, url, response, params, json_body, headers):
        """将请求和响应详情附加到 Allure 报告。"""
        try:
            allure.attach(
                json_module.dumps({
                    "method": method,
                    "url": url,
                    "params": params,
                    "body": json_body,
                    "headers": headers,
                }, ensure_ascii=False, indent=2),
                name="请求详情",
                attachment_type=allure.attachment_type.JSON,
            )
            allure.attach(
                json_module.dumps({
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.content else None,
                    "elapsed_ms": response.elapsed.total_seconds() * 1000,
                }, ensure_ascii=False, indent=2),
                name="响应详情",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            pass

    def close(self):
        """关闭Session。"""
        self.session.close()
        logger.info("HTTP Session 已关闭")
