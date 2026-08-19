"""Test/Utility 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class TestAPI(BaseAPI):
    """Test/Utility 模块 API，处理测试端点和IP查询。"""

    def __init__(self, client=None):
        super().__init__(client, "test")

    @allure.step("测试端点")
    def test_endpoint(self, method: str = "GET") -> dict:
        """
        测试端点，用于验证网络连通性。

        Args:
            method: HTTP方法

        Returns:
            {status: 'ok', method: 'GET'}
        """
        response = self.client.request(method, "/test")
        return response.json()

    @allure.step("获取IP地址")
    def get_ip(self) -> dict:
        """获取客户端IP地址和UserAgent。"""
        response = self.client.get("/ip")
        return response.json()
