"""
Test/Utility 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Utility 模块")
@pytest.mark.smoke
class TestUtilitySmoke:
    """Utility 模块冒烟测试用例。"""

    @allure.story("测试端点")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("/test 端点应返回状态ok")
    def test_test_endpoint(self, test_api):
        """验证 /test 端点返回状态ok。"""
        data = test_api.test_endpoint("GET")
        
        Assertions.assert_field_equals(data, "status", "ok")

    @allure.story("IP地址查询")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/ip 端点应返回IP地址")
    def test_get_ip(self, test_api):
        """验证 /ip 端点返回IP地址。"""
        data = test_api.get_ip()
        
        Assertions.assert_field_not_none(data, "ip")
