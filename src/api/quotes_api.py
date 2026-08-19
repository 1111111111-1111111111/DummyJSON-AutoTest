"""Quotes 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class QuotesAPI(BaseAPI):
    """Quotes 模块 API，处理名言查询、随机名言等。"""

    def __init__(self, client=None):
        super().__init__(client, "quotes")

    @allure.step("获取随机名言")
    def get_random(self) -> dict:
        """获取一条随机名言。"""
        response = self.client.get("/quotes/random")
        return response.json()
