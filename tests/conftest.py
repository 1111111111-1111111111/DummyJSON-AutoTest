"""
Pytest 全局配置和 Fixtures

提供全局可用的测试fixtures，包括 HTTP客户端、各模块API实例、
认证Token、关键字驱动等。

同时在测试失败时自动调用截图工具留存证据，
并集成超时重试机制（TimeoutException 自动重试 3 次，间隔 5 秒）。
"""
import time
import functools
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
from src.utils.retry import TimeoutException, retry_tracker


# ============================================================
# Pytest 配置：注册自定义标记
# ============================================================
def pytest_configure(config):
    """注册自定义 pytest 标记。"""
    config.addinivalue_line(
        "markers",
        "retry(max_attempts=3, delay=5): 超时自动重试标记，"
        "可自定义最大重试次数和重试间隔（秒）",
    )
    config.addinivalue_line(
        "markers",
        "timeout(seconds): 单个测试超时限制标记（秒）",
    )


# ============================================================
# 超时重试机制：在 collection 阶段包装所有测试函数
# 当测试抛出 TimeoutException 时自动重试（默认 3 次，间隔 5 秒）
# ============================================================
def _make_retry_wrapper(original_func, test_name, max_attempts, delay):
    """
    创建带有超时重试逻辑的测试函数包装器。

    使用工厂函数确保闭包正确捕获变量（避免循环变量延迟绑定问题）。
    """

    @functools.wraps(original_func)
    def retry_wrapper(*args, **kwargs):
        for attempt in range(1, max_attempts + 1):
            try:
                result = original_func(*args, **kwargs)
                if attempt > 1:
                    logger.info(
                        f"[重试] {test_name} 第 {attempt} 次执行成功 "
                        f"(之前失败 {attempt - 1} 次)"
                    )
                    retry_tracker.record(test_name, attempt, max_attempts, None, True)
                return result
            except TimeoutException as e:
                is_last = attempt >= max_attempts
                retry_tracker.record(test_name, attempt, max_attempts, e, False)

                if is_last:
                    logger.error(
                        f"[重试] {test_name} 超时重试已达上限({max_attempts}次)，最终失败 | "
                        f"异常: {e}"
                    )
                    raise
                else:
                    logger.warning(
                        f"[重试] {test_name} 超时(TimeoutException) | "
                        f"第 {attempt}/{max_attempts} 次 | "
                        f"{delay}s 后重试... | 异常: {e}"
                    )
                    time.sleep(delay)
            except Exception:
                # 非超时异常，不重试，直接抛出
                raise

    retry_wrapper._retry_wrapped = True
    return retry_wrapper


def pytest_collection_modifyitems(items):
    """
    在测试收集完成后，为每个测试函数添加超时重试包装。

    默认策略：所有测试在抛出 TimeoutException 时自动重试 3 次，间隔 5 秒。
    可通过 @pytest.mark.retry(max_attempts=N, delay=M) 自定义单个测试的重试参数。

    注意：对于 class-based 测试，需替换 class 上的方法（而非 item.obj），
    以确保 pytest 的描述符协议正确处理 self 绑定。
    """
    for item in items:
        if not isinstance(item, pytest.Function):
            continue

        # 跳过已包装的函数
        original_func = getattr(item, "function", None)
        if original_func is None or getattr(original_func, "_retry_wrapped", False):
            continue

        # 获取重试参数：优先使用 @pytest.mark.retry 标记，否则使用默认值
        retry_marker = item.get_closest_marker("retry")
        if retry_marker:
            max_attempts = retry_marker.kwargs.get("max_attempts", 3)
            delay = retry_marker.kwargs.get("delay", 5.0)
        else:
            max_attempts = 3
            delay = 5.0

        test_name = item.name
        wrapped = _make_retry_wrapper(original_func, test_name, max_attempts, delay)

        # class-based 测试：替换 class 上的方法，让 pytest 描述符协议处理 self 绑定
        if hasattr(item, "cls") and item.cls is not None and hasattr(item, "originalname"):
            setattr(item.cls, item.originalname, wrapped)
        else:
            # function-based 测试：直接替换 item.obj
            try:
                item.obj = wrapped
            except (AttributeError, TypeError):
                pass


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


# ============================================================
# Pytest Hook: 测试结束后输出重试统计
# ============================================================
def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束时输出超时重试统计摘要。

    在 CI/CD 中可用于判断测试稳定性，辅助分析不稳定用例。
    """
    summary = retry_tracker.get_summary()
    if summary["total_retry_events"] > 0:
        logger.info("=" * 60)
        logger.info("超时重试统计摘要")
        logger.info("=" * 60)
        logger.info(f"  总重试事件: {summary['total_retry_events']}")
        logger.info(f"  重试后成功: {summary['successful_after_retry']}")
        logger.info(f"  重试后仍失败: {summary['failed_after_retry']}")
        logger.info(f"  涉及测试数: {summary['tests_with_retries']}")
        logger.info(f"  重试率: {summary['retry_rate']}")
        logger.info("=" * 60)
    else:
        logger.debug("[重试统计] 本次测试无超时重试事件")
