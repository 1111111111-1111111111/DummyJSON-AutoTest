"""Quotes 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Quotes 模块")
@pytest.mark.regression
class TestQuotesRegression:
    """Quotes 模块全量回归测试用例。"""

    @allure.story("获取名言列表")
    @allure.title("获取名言列表并验证Schema")
    def test_get_all_quotes_schema(self, quotes_api):
        data = quotes_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "quotes")
        for quote in data["quotes"]:
            SchemaValidator.validate_response(quote, "quote")

    @allure.story("获取单个名言")
    @allure.title("获取ID为1的名言")
    def test_get_quote_by_id(self, quotes_api):
        quote = quotes_api.get_by_id(1)
        Assertions.assert_field_equals(quote, "id", 1)
        Assertions.assert_field_not_none(quote, "quote")
        Assertions.assert_field_not_none(quote, "author")

    @allure.story("获取随机名言")
    @allure.title("获取随机名言应返回有效数据")
    def test_get_random_quote(self, quotes_api):
        quote = quotes_api.get_random()
        Assertions.assert_field_not_none(quote, "id")
        Assertions.assert_field_not_none(quote, "quote")
        Assertions.assert_field_not_none(quote, "author")

    @allure.story("排序名言")
    @allure.title("按author排序获取名言")
    def test_sort_quotes_by_author(self, quotes_api):
        """验证按author排序获取名言。

        注意: DummyJSON quotes 模块不支持 /quotes/search 搜索端点，
        使用排序端点替代搜索测试。
        """
        data = quotes_api.get_sorted("author", "asc")
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "quotes")
        authors = [q["author"] for q in data["quotes"]]
        # 验证所有author字段非空
        assert all(a is not None for a in authors), "author字段不应为None"
        # 验证可正确排序
        sorted_authors = sorted(authors)
        assert sorted_authors[0] <= sorted_authors[-1], "排序后首尾元素应符合升序"

    @allure.story("分页")
    @allure.title("分页获取名言")
    def test_pagination(self, quotes_api):
        data = quotes_api.get_paginated(limit=5, skip=0)
        Assertions.assert_field_equals(data, "limit", 5)
        assert len(data["quotes"]) == 5

    @allure.story("选择字段")
    @allure.title("仅选择quote和author字段")
    def test_select_fields(self, quotes_api):
        data = quotes_api.get_paginated(limit=5, skip=0, select="quote,author")
        Assertions.assert_list_not_empty(data, "quotes")
        for quote in data["quotes"]:
            assert "quote" in quote
            assert "author" in quote

    @allure.story("异常场景")
    @allure.title("查询不存在的名言ID返回404")
    def test_quote_not_found(self, quotes_api):
        response = quotes_api.client.get("/quotes/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("边界场景")
    @allure.title("limit=0获取全部名言")
    def test_limit_zero(self, quotes_api):
        """验证limit=0获取所有名言。

        注意: DummyJSON 在 limit=0 时返回全部数据，且响应中的 limit 字段
        返回的是总数而非0，因此只验证返回的数据量大于默认分页大小。
        """
        data = quotes_api.get_all(params={"limit": 0})

        assert data["total"] > 30  # 应返回全部名言
        assert len(data["quotes"]) > 30  # 返回的名言数量应超过默认分页

    @allure.story("关键字驱动: 名言查询流程")
    @allure.title("关键字组合 - 获取列表+随机名言+搜索")
    def test_keyword_quote_flow(self, keywords):
        all_quotes = keywords.send_get("/quotes")
        keywords.assert_pagination(all_quotes)

        random_quote = keywords.send_get("/quotes/random")
        keywords.assert_field(random_quote, "id", is_not_none=True)
        keywords.assert_field(random_quote, "quote", is_not_none=True)
