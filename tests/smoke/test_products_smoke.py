"""
Products 模块冒烟测试

验证 Products 模块核心正向流程可用性。
"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Products 模块")
@pytest.mark.smoke
class TestProductsSmoke:
    """Products 模块冒烟测试用例。"""

    @allure.story("获取商品列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取商品列表应返回分页数据")
    def test_get_all_products(self, products_api):
        """验证获取商品列表返回分页结构。"""
        data = products_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "products")
        first_product = data["products"][0]
        SchemaValidator.validate_response(first_product, "product")

    @allure.story("获取单个商品")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取单个商品应返回正确商品")
    def test_get_single_product(self, products_api):
        """验证获取单个商品返回正确的商品信息。"""
        product = products_api.get_by_id(1)
        
        Assertions.assert_field_equals(product, "id", 1)
        Assertions.assert_field_not_none(product, "title")
        Assertions.assert_field_not_none(product, "price")
