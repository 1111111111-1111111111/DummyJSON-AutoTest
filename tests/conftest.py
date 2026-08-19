"""
Pytest 全局配置和 Fixtures

提供全局可用的测试fixtures，包括 HTTP客户端、各模块API实例、
认证Token、关键字驱动等。

同时在测试失败时自动调用截图工具留存证据。
"""
import json as json_module
import pytest
import allure
from src.core.http_client import HttpClient
from src.core.config_manager import config
from src.core.keyword_actions import KeywordActions
from src.core.data_generator import data_generator
from src.core.data_loader import DataLoader
from src.api.auth_api import AuthAPI
from src.api.products_api import ProductsAPI
from src.api.carts_api import CartsAPI
from src.api.users_api import UsersAPI
from src.api.posts_api import PostsAPI
from src.api.comments_api import CommentsAPI
from src.api.quotes_api import QuotesAPI
from src.api.recipes_api import RecipesAPI
from src.api.todos_api import TodosAPI
from src.api.test_api import TestAPI
from src.core.logger import logger
from src.utils.screenshot import ScreenshotUtil


@pytest.fixture(scope="session")
def http_client():
    """全局 HTTP 客户端（session级，所有测试共享）。"""
    client = HttpClient()
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_api(http_client):
    """Auth API 实例。"""
    return AuthAPI(client=http_client)


@pytest.fixture(scope="session")
def products_api(http_client):
    """Products API 实例。"""
    return ProductsAPI(client=http_client)


@pytest.fixture(scope="session")
def carts_api(http_client):
    """Carts API 实例。"""
    return CartsAPI(client=http_client)


@pytest.fixture(scope="session")
def users_api(http_client):
    """Users API 实例。"""
    return UsersAPI(client=http_client)


@pytest.fixture(scope="session")
def posts_api(http_client):
    """Posts API 实例。"""
    return PostsAPI(client=http_client)


@pytest.fixture(scope="session")
def comments_api(http_client):
    """Comments API 实例。"""
    return CommentsAPI(client=http_client)


@pytest.fixture(scope="session")
def quotes_api(http_client):
    """Quotes API 实例。"""
    return QuotesAPI(client=http_client)


@pytest.fixture(scope="session")
def recipes_api(http_client):
    """Recipes API 实例。"""
    return RecipesAPI(client=http_client)


@pytest.fixture(scope="session")
def todos_api(http_client):
    """Todos API 实例。"""
    return TodosAPI(client=http_client)


@pytest.fixture(scope="session")
def test_api(http_client):
    """Test/Utility API 实例。"""
    return TestAPI(client=http_client)


@pytest.fixture(scope="session")
def keywords(http_client):
    """关键字驱动实例。"""
    return KeywordActions(client=http_client)


@pytest.fixture(scope="session")
def auth_token(auth_api):
    """登录获取认证Token（session级，所有测试共享）。"""
    creds = config.auth_credentials
    login_data = auth_api.login(
        username=creds["username"],
        password=creds["password"],
        expires_in_mins=60,
    )
    token = login_data.get("accessToken")
    assert token, "登录应返回 accessToken"
    logger.info(f"全局认证Token获取成功: {creds['username']}")
    return token


@pytest.fixture(scope="session", autouse=True)
def setup_auth(http_client, auth_token):
    """自动设置全局认证Token。"""
    http_client.set_token(auth_token)
    yield


@pytest.fixture
def product_data():
    """加载产品测试数据（YAML）。"""
    return DataLoader.load_yaml("products/product_data.yaml")


@pytest.fixture
def product_json_data():
    """加载产品测试数据（JSON）。"""
    return DataLoader.load_json("products/product_data.json")


@pytest.fixture
def login_data():
    """加载认证测试数据。"""
    return DataLoader.load_yaml("auth/login_data.yaml")


@pytest.fixture
def cart_data():
    """加载购物车测试数据。"""
    return DataLoader.load_yaml("carts/cart_data.yaml")


@pytest.fixture
def user_data():
    """加载用户测试数据。"""
    return DataLoader.load_yaml("users/user_data.yaml")


@pytest.fixture
def post_data():
    """加载帖子测试数据。"""
    return DataLoader.load_yaml("posts/post_data.yaml")


@pytest.fixture
def comment_data():
    """加载评论测试数据。"""
    return DataLoader.load_yaml("comments/comment_data.yaml")


@pytest.fixture
def quote_data():
    """加载名言测试数据。"""
    return DataLoader.load_yaml("quotes/quote_data.yaml")


@pytest.fixture
def recipe_data():
    """加载食谱测试数据。"""
    return DataLoader.load_yaml("recipes/recipe_data.yaml")


@pytest.fixture
def todo_data():
    """加载待办测试数据。"""
    return DataLoader.load_yaml("todos/todo_data.yaml")


@pytest.fixture
def gen():
    """数据生成器实例。"""
    return data_generator


# ============================================================
# Pytest Hook: 测试失败时自动截图留存证据
# ============================================================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试执行后生成报告钩子。

    当测试在 call 阶段失败时，自动调用 ScreenshotUtil 留存断言失败证据：
      - 测试用例名称、时间戳
      - 断言错误类型与错误消息
      - 异常堆栈追踪
      - 最近的 HTTP 请求/响应上下文
    """
    outcome = yield
    report = outcome.get_result()

    # 仅在 call 阶段（实际执行测试函数）失败时触发
    if report.when == "call" and report.failed:
        test_name = item.name
        # 从 funcargs 中获取 http_client 实例（session 级 fixture）
        http_client = item.funcargs.get("http_client") if hasattr(item, "funcargs") else None

        request_context = None
        response_context = None

        if http_client is not None:
            # 提取请求上下文
            request_context = http_client.last_request

            # 从 Response 对象提取响应上下文
            if http_client.last_response is not None:
                resp = http_client.last_response
                try:
                    body = resp.json() if resp.content else None
                except Exception:
                    body = resp.text[:2000] if resp.text else None

                response_context = {
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "body": body,
                    "elapsed_ms": round(resp.elapsed.total_seconds() * 1000, 2),
                    "url": resp.url,
                }

        # 获取异常对象
        error_info = call.excinfo.value if call.excinfo else Exception("Unknown error")

        # 调用截图工具留存证据
        try:
            ScreenshotUtil.capture_failure(
                test_name=test_name,
                error_info=error_info,
                request_context=request_context,
                response_context=response_context,
            )
        except Exception as e:
            logger.warning(f"截图工具执行异常（不影响测试结果）: {e}")
