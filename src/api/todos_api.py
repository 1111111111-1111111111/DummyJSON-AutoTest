"""Todos 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class TodosAPI(BaseAPI):
    """Todos 模块 API，处理待办事项CRUD。"""

    def __init__(self, client=None):
        super().__init__(client, "todos")

    @allure.step("获取随机待办")
    def get_random(self) -> dict:
        """获取一条随机待办事项。"""
        response = self.client.get("/todos/random")
        return response.json()

    @allure.step("获取用户待办: user_id={user_id}")
    def get_by_user(self, user_id: int) -> dict:
        """获取指定用户的待办事项。"""
        response = self.client.get(f"/todos/user/{user_id}")
        return response.json()
