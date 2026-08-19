"""
Auth 模块冒烟测试

验证 Auth 模块核心正向流程可用性。
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Auth 模块")
@pytest.mark.smoke
class TestAuthSmoke:
    """Auth 模块冒烟测试用例。"""

    @allure.story("用户登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("使用有效凭据登录应成功")
    def test_login_valid_credentials(self, auth_api):
        """验证使用有效凭据登录返回200和Token。"""
        response = auth_api.login("emilys", "emilyspass")
        
        Assertions.assert_field_not_none(response, "id")
        Assertions.assert_field_equals(response, "username", "emilys")
        Assertions.assert_field_not_none(response, "accessToken")
        Assertions.assert_field_not_none(response, "refreshToken")

    @allure.story("获取当前用户")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("使用Token获取当前用户信息")
    def test_get_current_user(self, auth_api, auth_token):
        """验证使用Token获取当前用户信息返回200和正确用户。"""
        user = auth_api.get_current_user()
        
        Assertions.assert_field_not_none(user, "id")
        Assertions.assert_field_not_none(user, "username")
        Assertions.assert_field_not_none(user, "email")
