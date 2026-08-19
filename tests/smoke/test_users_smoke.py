"""
Users 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Users 模块")
@pytest.mark.smoke
class TestUsersSmoke:
    """Users 模块冒烟测试用例。"""

    @allure.story("获取用户列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取用户列表应返回分页数据")
    def test_get_all_users(self, users_api):
        """验证获取用户列表返回分页结构。"""
        data = users_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "users")

    @allure.story("获取单个用户")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取单个用户应返回正确用户")
    def test_get_single_user(self, users_api):
        """验证获取单个用户返回正确的用户信息。"""
        user = users_api.get_by_id(1)
        
        Assertions.assert_field_equals(user, "id", 1)
        Assertions.assert_field_not_none(user, "firstName")
        Assertions.assert_field_not_none(user, "lastName")
