"""Carts 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class CartsAPI(BaseAPI):
    """Carts 模块 API，处理购物车CRUD。"""

    def __init__(self, client=None):
        super().__init__(client, "carts")

    @allure.step("获取用户购物车: user_id={user_id}")
    def get_user_carts(self, user_id: int) -> dict:
        """获取指定用户的购物车。"""
        response = self.client.get(f"/carts/user/{user_id}")
        return response.json()
