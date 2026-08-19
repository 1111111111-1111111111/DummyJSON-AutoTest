"""Users 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class UsersAPI(BaseAPI):
    """Users 模块 API，处理用户CRUD、搜索、过滤等。"""

    def __init__(self, client=None):
        super().__init__(client, "users")

    @allure.step("过滤用户: key={key} value={value}")
    def filter_users(self, key: str, value: str) -> dict:
        """过滤用户（支持嵌套键，如 hair.color）。"""
        response = self.client.get("/users/filter", params={"key": key, "value": value})
        return response.json()

    @allure.step("获取用户购物车: user_id={user_id}")
    def get_user_carts(self, user_id: int) -> dict:
        """获取用户的购物车。"""
        response = self.client.get(f"/users/{user_id}/carts")
        return response.json()

    @allure.step("获取用户帖子: user_id={user_id}")
    def get_user_posts(self, user_id: int) -> dict:
        """获取用户的帖子。"""
        response = self.client.get(f"/users/{user_id}/posts")
        return response.json()

    @allure.step("获取用户待办: user_id={user_id}")
    def get_user_todos(self, user_id: int) -> dict:
        """获取用户的待办事项。"""
        response = self.client.get(f"/users/{user_id}/todos")
        return response.json()
