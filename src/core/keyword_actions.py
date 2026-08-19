"""
关键字驱动函数封装

将常用的 API 操作封装为关键字，支持通过关键字组合编写测试用例。
"""
import allure
from src.core.logger import logger
from src.core.http_client import HttpClient
from src.core.schema_validator import SchemaValidator


class KeywordActions:
    """
    关键字驱动

    将常用操作封装为可复用的关键字方法，
    支持链式调用和数据驱动组合。
    """

    def __init__(self, client: HttpClient = None):
        """
        初始化关键字驱动。

        Args:
            client: HTTP客户端实例，不传则自动创建
        """
        self.client = client or HttpClient()

    @allure.step("发送GET请求: {endpoint}")
    def send_get(self, endpoint: str, params: dict = None) -> dict:
        """
        关键字: 发送GET请求。

        Args:
            endpoint: API端点
            params: 查询参数

        Returns:
            响应JSON数据
        """
        response = self.client.get(endpoint, params=params)
        return response.json()

    @allure.step("发送POST请求: {endpoint}")
    def send_post(self, endpoint: str, body: dict = None) -> dict:
        """
        关键字: 发送POST请求。

        Args:
            endpoint: API端点
            body: 请求体

        Returns:
            响应JSON数据
        """
        response = self.client.post(endpoint, json=body)
        return response.json()

    @allure.step("发送PUT请求: {endpoint}")
    def send_put(self, endpoint: str, body: dict = None) -> dict:
        """关键字: 发送PUT请求。"""
        response = self.client.put(endpoint, json=body)
        return response.json()

    @allure.step("发送PATCH请求: {endpoint}")
    def send_patch(self, endpoint: str, body: dict = None) -> dict:
        """关键字: 发送PATCH请求。"""
        response = self.client.patch(endpoint, json=body)
        return response.json()

    @allure.step("发送DELETE请求: {endpoint}")
    def send_delete(self, endpoint: str) -> dict:
        """关键字: 发送DELETE请求。"""
        response = self.client.delete(endpoint)
        return response.json()

    @allure.step("验证状态码: 期望={expected_code}")
    def assert_status_code(self, response, expected_code: int):
        """
        关键字: 验证HTTP状态码。

        Args:
            response: 响应对象
            expected_code: 期望状态码
        """
        actual_code = response.status_code if hasattr(response, 'status_code') else response
        logger.info(f"状态码验证: 期望={expected_code} 实际={actual_code}")
        assert actual_code == expected_code, f"状态码不匹配: 期望={expected_code} 实际={actual_code}"

    @allure.step("验证响应字段: {field} 期望={expected_value}")
    def assert_field(self, data: dict, field: str, expected_value=None, is_not_none: bool = False):
        """
        关键字: 验证响应字段值。

        Args:
            data: 响应数据
            field: 字段名
            expected_value: 期望值
            is_not_none: 是否仅验证非空
        """
        if is_not_none:
            assert field in data and data[field] is not None, f"字段 '{field}' 应非空"
            logger.info(f"字段非空验证通过: {field}")
        else:
            assert data.get(field) == expected_value, f"字段 '{field}' 值不匹配: 期望={expected_value} 实际={data.get(field)}"
            logger.info(f"字段值验证通过: {field}={expected_value}")

    @allure.step("验证响应包含列表: key={key}")
    def assert_has_list(self, data: dict, key: str, min_count: int = 1):
        """
        关键字: 验证响应包含指定列表且有最小数量。

        Args:
            data: 响应数据
            key: 列表字段名
            min_count: 最小元素数量
        """
        assert key in data, f"响应应包含字段 '{key}'"
        assert isinstance(data[key], list), f"字段 '{key}' 应为列表类型"
        assert len(data[key]) >= min_count, f"列表 '{key}' 应至少有 {min_count} 个元素, 实际有 {len(data[key])}"
        logger.info(f"列表验证通过: {key} 有 {len(data[key])} 个元素")

    @allure.step("验证分页字段")
    def assert_pagination(self, data: dict):
        """关键字: 验证分页响应结构。"""
        SchemaValidator.validate_response(data, "paginated")
        logger.info("分页结构验证通过")

    @allure.step("验证JSON Schema: {resource_type}")
    def assert_schema(self, data: dict, resource_type: str):
        """
        关键字: 验证JSON Schema。

        Args:
            data: 响应数据
            resource_type: 资源类型
        """
        SchemaValidator.validate_response(data, resource_type)
        logger.info(f"Schema 验证通过: {resource_type}")

    @allure.step("提取响应字段: {field}")
    def extract_field(self, data: dict, field: str):
        """
        关键字: 从响应中提取字段值。

        Args:
            data: 响应数据
            field: 字段名

        Returns:
            字段值
        """
        value = data.get(field)
        logger.info(f"提取字段: {field}={value}")
        return value

    @allure.step("登录获取Token")
    def login_and_get_token(self, username: str, password: str) -> str:
        """
        关键字: 登录获取Token。

        Args:
            username: 用户名
            password: 密码

        Returns:
            accessToken
        """
        response = self.client.post("/auth/login", json={
            "username": username,
            "password": password,
            "expiresInMins": 30,
        })
        data = response.json()
        token = data.get("accessToken")
        assert token, "登录应返回 accessToken"
        self.client.set_token(token)
        logger.info(f"登录成功: username={username}")
        return token

    @allure.step("验证鉴权失败")
    def assert_unauthorized(self, endpoint: str):
        """
        关键字: 验证无Token时鉴权失败。

        Args:
            endpoint: 需要鉴权的端点
        """
        # 临时清除Token
        saved_token = self.client.token
        self.client.session.headers.pop("Authorization", None)
        self.client._access_token = None
        response = self.client.get(endpoint)
        self.client.set_token(saved_token) if saved_token else None
        assert response.status_code == 401, f"无Token应返回401, 实际={response.status_code}"
        logger.info("鉴权失败验证通过: 返回401")
