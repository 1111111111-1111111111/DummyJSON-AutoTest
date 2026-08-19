"""断言工具模块 - 提供丰富的断言函数。"""
from src.core.logger import logger


class Assertions:
    """断言工具类，提供通用断言方法。"""

    @staticmethod
    def assert_status_code(response, expected_code: int):
        actual = response.status_code
        assert actual == expected_code, f"状态码不匹配 | 期望={expected_code} 实际={actual} | 响应体={response.text[:500]}"
        logger.info(f"断言通过: 状态码={actual}")

    @staticmethod
    def assert_field_equals(data: dict, field: str, expected_value):
        actual = data.get(field)
        assert actual == expected_value, f"字段值不匹配 | field={field} | 期望={expected_value} 实际={actual}"
        logger.info(f"断言通过: {field}={actual}")

    @staticmethod
    def assert_field_not_none(data: dict, field: str):
        assert field in data, f"响应应包含字段 '{field}'"
        assert data[field] is not None, f"字段 '{field}' 不应为 None"
        logger.info(f"断言通过: {field} 非空")

    @staticmethod
    def assert_field_in(data: dict, field: str):
        assert field in data, f"响应应包含字段 '{field}'"
        logger.info(f"断言通过: 包含字段 '{field}'")

    @staticmethod
    def assert_list_not_empty(data: dict, key: str):
        assert key in data, f"响应应包含字段 '{key}'"
        assert isinstance(data[key], list), f"字段 '{key}' 应为列表"
        assert len(data[key]) > 0, f"列表 '{key}' 不应为空"
        logger.info(f"断言通过: 列表 '{key}' 有 {len(data[key])} 个元素")

    @staticmethod
    def assert_pagination_fields(data: dict):
        for field in ["total", "skip", "limit"]:
            assert field in data, f"分页响应应包含 '{field}'"
        logger.info(f"断言通过: 分页字段完整 (total={data['total']}, skip={data['skip']}, limit={data['limit']})")

    @staticmethod
    def assert_response_time(response, max_seconds: float = 5.0):
        elapsed = response.elapsed.total_seconds()
        assert elapsed <= max_seconds, f"响应时间过长 | 耗时={elapsed:.3f}s | 上限={max_seconds}s"
        logger.info(f"断言通过: 响应时间={elapsed:.3f}s")
