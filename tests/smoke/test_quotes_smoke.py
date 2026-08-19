"""
Quotes 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Quotes 模块")
@pytest.mark.smoke
class TestQuotesSmoke:
    """Quotes 模块冒烟测试用例。"""

    @allure.story("获取名言列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取名言列表应返回分页数据")
    def test_get_all_quotes(self, quotes_api):
        """验证获取名言列表返回分页结构。"""
        data = quotes_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "quotes")

    @allure.story("获取随机名言")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取随机名言应返回有效数据")
    def test_get_random_quote(self, quotes_api):
        """验证获取随机名言返回有效的名言数据。"""
        quote = quotes_api.get_random()
        
        Assertions.assert_field_not_none(quote, "id")
        Assertions.assert_field_not_none(quote, "quote")
        Assertions.assert_field_not_none(quote, "author")
