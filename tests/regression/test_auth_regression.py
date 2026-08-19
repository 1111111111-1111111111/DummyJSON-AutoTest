"""
Auth 模块回归测试

覆盖 Auth 模块所有接口的正向、异常、边界、鉴权场景。
包含数据驱动测试。
"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator
from src.core.data_loader import DataLoader


@allure.epic("DummyJSON API")
@allure.feature("Auth 模块")
@pytest.mark.regression
class TestAuthRegression:
    """Auth 模块全量回归测试用例。"""

    @allure.story("数据驱动登录测试")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("数据驱动登录场景 - {test_id}")
    @pytest.mark.parametrize("case", DataLoader.load_yaml("auth/login_data.yaml"))
    def test_login_data_driven(self, auth_api, case):
        """使用YAML数据驱动测试多种登录场景。"""
        response = auth_api.client.post("/auth/login", json={
            "username": case["username"],
            "password": case["password"],
        })

        if case.get("expected_status") == 200:
            Assertions.assert_status_code(response, 200)
            data = response.json()
            for field in case.get("expected_fields", []):
                Assertions.assert_field_not_none(data, field)
            SchemaValidator.validate_response(data, "auth_login")
        else:
            assert response.status_code in (400, 404), f"期望400/404, 实际={response.status_code}"

    @allure.story("获取当前用户")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取当前用户应返回完整用户信息")
    def test_get_current_user_full(self, auth_api):
        """验证获取当前用户返回完整的用户信息。"""
        user = auth_api.get_current_user()

        Assertions.assert_field_not_none(user, "id")
        Assertions.assert_field_not_none(user, "username")
        Assertions.assert_field_not_none(user, "email")
        Assertions.assert_field_not_none(user, "firstName")
        Assertions.assert_field_not_none(user, "lastName")

    @allure.story("刷新Token")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("刷新Token应返回新的accessToken")
    def test_refresh_token(self, auth_api, auth_token):
        """验证刷新Token返回新的accessToken和refreshToken。"""
        login_data = auth_api.login("emilys", "emilyspass")
        refresh_token = login_data.get("refreshToken")

        result = auth_api.refresh_token(refresh_token)

        Assertions.assert_field_not_none(result, "accessToken")
        Assertions.assert_field_not_none(result, "refreshToken")

    @allure.story("鉴权失败")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("无Token访问/auth/me应返回401")
    def test_auth_me_without_token(self, http_client):
        """验证无Token访问需要鉴权的端点返回401。"""
        # 创建一个没有Token的客户端
        from src.core.http_client import HttpClient
        no_auth_client = HttpClient()
        no_auth_client._access_token = None
        no_auth_client.session.headers.pop("Authorization", None)

        response = no_auth_client.get("/auth/me")
        Assertions.assert_status_code(response, 401)
        no_auth_client.close()

    @allure.story("User端点登录")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/user/login 端点登录")
    def test_user_login_endpoint(self, auth_api):
        """验证 /user/login 端点登录功能。"""
        data = auth_api.user_login("emilys", "emilyspass")

        Assertions.assert_field_not_none(data, "accessToken")
        Assertions.assert_field_not_none(data, "refreshToken")
        Assertions.assert_field_not_none(data, "id")

    @allure.story("User端点获取当前用户")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/user/me 端点获取当前用户")
    def test_user_me_endpoint(self, auth_api):
        """验证 /user/me 端点获取当前用户功能。"""
        user = auth_api.get_user_me()

        Assertions.assert_field_not_none(user, "id")
        Assertions.assert_field_not_none(user, "firstName")

    @allure.story("Token过期时间")
    @allure.severity(allure.severity_level.MINOR)
    @allure.title("指定expiresInMins=1的Token")
    def test_login_with_short_expiry(self, auth_api):
        """验证指定短过期时间的Token。"""
        data = auth_api.login("emilys", "emilyspass", expires_in_mins=1)

        Assertions.assert_field_not_none(data, "accessToken")
        Assertions.assert_field_not_none(data, "refreshToken")

    @allure.story("关键字驱动: 登录+获取用户组合")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("关键字组合 - 登录并验证用户")
    def test_keyword_login_and_verify(self, keywords):
        """使用关键字组合：登录获取Token -> 验证获取当前用户。"""
        token = keywords.login_and_get_token("emilys", "emilyspass")
        assert token, "关键字登录应返回Token"

        user_data = keywords.send_get("/auth/me")
        keywords.assert_field(user_data, "username", "emilys")
        keywords.assert_field(user_data, "id", is_not_none=True)
