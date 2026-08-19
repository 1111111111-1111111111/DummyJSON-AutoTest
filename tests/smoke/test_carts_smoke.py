"""
Carts 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Carts 模块")
@pytest.mark.smoke
class TestCartsSmoke:
    """Carts 模块冒烟测试用例。"""

    @allure.story("获取购物车列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取购物车列表应返回分页数据")
    def test_get_all_carts(self, carts_api):
        """验证获取购物车列表返回分页结构。"""
        data = carts_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "carts")

    @allure.story("获取单个购物车")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取单个购物车应返回正确数据")
    def test_get_single_cart(self, carts_api):
        """验证获取单个购物车返回正确的购物车信息。"""
        cart = carts_api.get_by_id(1)
        
        Assertions.assert_field_equals(cart, "id", 1)
        Assertions.assert_field_not_none(cart, "products")
        Assertions.assert_field_not_none(cart, "userId")
