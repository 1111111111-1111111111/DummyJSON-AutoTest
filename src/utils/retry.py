"""
超时重试机制

提供测试级别和请求级别的超时重试能力：
  1. @retry 装饰器：对函数进行自动重试，捕获指定异常类型
  2. @retry_on_timeout：专门处理 TimeoutException 的快捷装饰器
  3. pytest 标记 @pytest.mark.retry(max_attempts=3, delay=5)：测试级别重试
  4. timeout_context：上下文管理器，超时后抛出 TimeoutException

设计原则（参考 CI/CD 测试策略）：
  - 最多重试 3 次，每次间隔 5 秒（可通过参数自定义）
  - 重试时记录详细日志（尝试次数/异常类型/等待时间）
  - 所有重试失败后抛出最后一次异常
  - 不吞没异常，仅对指定类型重试（默认 TimeoutException）
"""
import time
import functools
import signal
import threading
from datetime import datetime
from typing import Callable, Type, Tuple, Optional

from src.core.logger import logger


class TimeoutException(Exception):
    """测试或请求超时异常。"""

    pass


def retry(
    max_attempts: int = 3,
    delay: float = 5.0,
    exceptions: Tuple[Type[Exception], ...] = (TimeoutException,),
    backoff: float = 1.0,
):
    """
    通用重试装饰器。

    在函数抛出指定异常时自动重试，最多重试 max_attempts 次，
    每次重试前等待 delay 秒（支持指数退避）。

    Args:
        max_attempts: 最大尝试次数（含首次），默认 3
        delay: 每次重试前等待秒数，默认 5.0
        exceptions: 触发重试的异常类型元组，默认 (TimeoutException,)
        backoff: 退避系数，每次重试 delay *= backoff，默认 1.0（等间隔）

    Returns:
        装饰器函数

    用法:
        @retry(max_attempts=3, delay=5, exceptions=(TimeoutException, ConnectionError))
        def test_api_call():
            ...

        @retry_on_timeout(max_attempts=3, delay=5)
        def test_slow_endpoint():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(
                            f"[重试] {func.__name__} 第 {attempt} 次尝试成功 "
                            f"(之前失败 {attempt - 1} 次)"
                        )
                    return result

                except exceptions as e:
                    last_exception = e
                    is_last_attempt = attempt >= max_attempts

                    if is_last_attempt:
                        logger.error(
                            f"[重试] {func.__name__} 已达最大重试次数 "
                            f"({max_attempts})，最终失败 | 异常: {type(e).__name__}: {e}"
                        )
                        raise

                    logger.warning(
                        f"[重试] {func.__name__} 第 {attempt}/{max_attempts} 次失败 "
                        f"| 异常: {type(e).__name__}: {e} "
                        f"| {current_delay}s 后重试..."
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

                except Exception as e:
                    # 非目标异常类型，直接抛出不重试
                    logger.debug(
                        f"[重试] {func.__name__} 抛出非目标异常 "
                        f"{type(e).__name__}，不重试"
                    )
                    raise

            # 理论上不会执行到这里
            raise last_exception

        return wrapper

    return decorator


def retry_on_timeout(max_attempts: int = 3, delay: float = 5.0):
    """
    超时重试装饰器（retry 的快捷版本，专门处理 TimeoutException）。

    Args:
        max_attempts: 最大尝试次数，默认 3
        delay: 每次重试间隔秒数，默认 5.0

    用法:
        @retry_on_timeout(max_attempts=3, delay=5)
        def test_long_running_api():
            response = client.get("/slow-endpoint", timeout=10)
            assert response.status_code == 200
    """
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        exceptions=(TimeoutException,),
    )


def timeout_context(seconds: float):
    """
    超时上下文管理器（基于线程实现，跨平台兼容）。

    在指定秒数内未完成则抛出 TimeoutException。

    Args:
        seconds: 超时秒数

    用法:
        with timeout_context(30):
            response = client.get("/slow-endpoint")
            assert response.status_code == 200
    """

    class _TimeoutContext:
        def __init__(self, timeout):
            self.timeout = timeout
            self._timer = None
            self._timed_out = False

        def __enter__(self):
            self._timed_out = False

            def _handler():
                self._timed_out = True
                logger.error(
                    f"[超时] 操作超过 {self.timeout}s 限制，触发 TimeoutException"
                )

            self._timer = threading.Timer(self.timeout, _handler)
            self._timer.daemon = True
            self._timer.start()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._timer:
                self._timer.cancel()
            if self._timed_out and exc_type is None:
                raise TimeoutException(
                    f"操作在 {self.timeout}s 后超时"
                )
            return False

    return _TimeoutContext(seconds)


def timeout(seconds: float):
    """
    函数超时装饰器（基于线程，跨平台兼容）。

    如果函数在指定秒数内未完成，抛出 TimeoutException。
    可与 @retry_on_timeout 组合使用实现「超时+重试」。

    Args:
        seconds: 超时秒数

    用法:
        @retry_on_timeout(max_attempts=3, delay=5)
        @timeout(30)
        def test_api_with_timeout():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = {"value": None, "exception": None}
            thread_started = threading.Event()
            thread_finished = threading.Event()

            def _target():
                try:
                    result["value"] = func(*args, **kwargs)
                except Exception as e:
                    result["exception"] = e
                finally:
                    thread_finished.set()

            t = threading.Thread(target=_target, daemon=True)
            t.start()
            thread_started.set()

            if not thread_finished.wait(timeout=seconds):
                logger.error(
                    f"[超时] {func.__name__} 在 {seconds}s 后超时"
                )
                raise TimeoutException(
                    f"函数 {func.__name__} 在 {seconds}s 后超时"
                )

            if result["exception"]:
                raise result["exception"]
            return result["value"]

        return wrapper

    return decorator


class RetryTracker:
    """
    重试追踪器：记录测试执行过程中的重试统计。

    在 CI/CD 中可用于汇总重试信息，判断测试稳定性。
    """

    def __init__(self):
        self._records = []

    def record(
        self,
        test_name: str,
        attempt: int,
        max_attempts: int,
        exception: Optional[Exception],
        success: bool,
    ):
        """记录一次重试事件。"""
        self._records.append(
            {
                "test_name": test_name,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "exception_type": type(exception).__name__ if exception else None,
                "exception_message": str(exception) if exception else None,
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_summary(self) -> dict:
        """获取重试统计摘要。"""
        total_retries = len(self._records)
        successful_retries = sum(1 for r in self._records if r["success"])
        failed_retries = total_retries - successful_retries
        tests_with_retries = len(set(r["test_name"] for r in self._records))

        return {
            "total_retry_events": total_retries,
            "successful_after_retry": successful_retries,
            "failed_after_retry": failed_retries,
            "tests_with_retries": tests_with_retries,
            "retry_rate": f"{(total_retries / max(tests_with_retries, 1)) * 100:.1f}%",
        }

    def log_summary(self):
        """输出重试统计到日志。"""
        summary = self.get_summary()
        logger.info(
            f"[重试统计] 总重试事件={summary['total_retry_events']} | "
            f"重试后成功={summary['successful_after_retry']} | "
            f"重试后仍失败={summary['failed_after_retry']} | "
            f"涉及测试数={summary['tests_with_retries']} | "
            f"重试率={summary['retry_rate']}"
        )


# 全局重试追踪器实例（可在 conftest.py 中引用）
retry_tracker = RetryTracker()
