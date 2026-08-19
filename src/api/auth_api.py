"""Auth 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI
from src.core.logger import logger


class AuthAPI(BaseAPI):
    """Auth 模块 API，处理登录、获取当前用户、刷新Token等。"""

    def __init__(self, client=None):
        super().__init__(client, "auth")

    @allure.step("用户登录")
    def login(self, username: str, password: str, expires_in_mins: int = 60) -> dict:
        """
        用户登录获取Token。

        Args:
            username: 用户名
            password: 密码
            expires_in_mins: Token过期时间（分钟）

        Returns:
            包含 accessToken 和 refreshToken 的登录信息
        """
        response = self.client.post("/auth/login", json={
            "username": username,
            "password": password,
            "expiresInMins": expires_in_mins,
        })
        return response.json()

    @allure.step("获取当前登录用户")
    def get_current_user(self) -> dict:
        """
        获取当前登录用户信息（需要Token）。

        Returns:
            当前用户详情
        """
        response = self.client.get("/auth/me")
        return response.json()

    @allure.step("刷新Token")
    def refresh_token(self, refresh_token: str = None) -> dict:
        """
        刷新Token。

        Args:
            refresh_token: refreshToken，不传则使用Cookie

        Returns:
            新的 accessToken 和 refreshToken
        """
        body = {}
        if refresh_token:
            body["refreshToken"] = refresh_token
        body["expiresInMins"] = 30
        response = self.client.post("/auth/refresh", json=body)
        return response.json()

    @allure.step("用户登录（user端点）")
    def user_login(self, username: str, password: str, expires_in_mins: int = 60) -> dict:
        """使用 /user/login 端点登录。"""
        response = self.client.post("/user/login", json={
            "username": username,
            "password": password,
            "expiresInMins": expires_in_mins,
        })
        return response.json()

    @allure.step("获取当前用户（user端点）")
    def get_user_me(self) -> dict:
        """使用 /user/me 端点获取当前用户。"""
        response = self.client.get("/user/me")
        return response.json()
