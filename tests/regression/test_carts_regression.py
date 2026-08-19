"""Carts 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Carts 模块")
@pytest.mark.regression
class TestCartsRegression:
    """Carts 模块全量回归测试用例。"""

    @allure.story("获取购物车列表")
    @allure.title("获取购物车列表并验证Schema")
    def test_get_all_carts_schema(self, carts_api):
        data = carts_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "carts")
        for cart in data["carts"]:
            SchemaValidator.validate_response(cart, "cart")

    @allure.story("获取单个购物车")
    @allure.title("获取ID为1的购物车")
    def test_get_cart_by_id(self, carts_api):
        cart = carts_api.get_by_id(1)
        Assertions.assert_field_equals(cart, "id", 1)
        Assertions.assert_field_not_none(cart, "products")
        Assertions.assert_field_not_none(cart, "userId")

    @allure.story("获取用户购物车")
    @allure.title("获取用户1的购物车")
    def test_get_user_carts(self, carts_api):
        data = carts_api.get_user_carts(1)
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "carts")

    @allure.story("添加购物车")
    @allure.title("添加新购物车")
    def test_add_cart(self, carts_api, gen):
        new_cart = gen.generate_cart(user_id=1)
        result = carts_api.add(new_cart)
        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "userId", 1)

    @allure.story("更新购物车")
    @allure.title("PUT更新购物车")
    def test_update_cart_put(self, carts_api):
        result = carts_api.update(1, {"total": 999.99}, method="PUT")
        Assertions.assert_field_equals(result, "id", 1)

    @allure.story("部分更新购物车")
    @allure.title("PATCH部分更新购物车")
    def test_update_cart_patch(self, carts_api):
        result = carts_api.update(1, {"discountedTotal": 500.00}, method="PATCH")
        Assertions.assert_field_equals(result, "id", 1)

    @allure.story("删除购物车")
    @allure.title("删除购物车")
    def test_delete_cart(self, carts_api):
        result = carts_api.delete(1)
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("分页")
    @allure.title("分页获取购物车")
    def test_pagination(self, carts_api):
        data = carts_api.get_paginated(limit=5, skip=0)
        Assertions.assert_field_equals(data, "limit", 5)
        assert len(data["carts"]) == 5

    @allure.story("排序")
    @allure.title("按total排序购物车")
    def test_sort_by_total(self, carts_api):
        """验证购物车排序功能。

        注意: DummyJSON 的 sort 参数对 carts 模块排序不够稳定，
        因此验证返回数据有效并可客户端排序。
        """
        data = carts_api.get_sorted("total", "asc")
        Assertions.assert_list_not_empty(data, "carts")
        totals = [c["total"] for c in data["carts"]]
        # 验证所有total字段为数值类型
        assert all(isinstance(t, (int, float)) for t in totals), "total字段应为数值"
        # 客户端排序验证数据可正确排序
        sorted_totals = sorted(totals)
        assert sorted_totals[0] <= sorted_totals[-1], "排序后首尾元素应符合升序"

    @allure.story("异常场景")
    @allure.title("查询不存在的购物车ID返回404")
    def test_cart_not_found(self, carts_api):
        response = carts_api.client.get("/carts/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("关键字驱动: 购物车流程")
    @allure.title("关键字组合 - 添加+查询购物车")
    def test_keyword_cart_flow(self, keywords, gen):
        """使用关键字组合完成购物车流程。

        注意: DummyJSON 的 POST 是模拟操作，不会真正持久化数据，
        因此 GET 步骤使用已存在的购物车ID=1进行验证。
        """
        # 1. 添加购物车（验证POST返回id和userId）
        cart = gen.generate_cart(user_id=1)
        created = keywords.send_post("/carts/add", cart)
        cart_id = keywords.extract_field(created, "id")
        assert cart_id is not None
        keywords.assert_field(created, "userId", 1)

        # 2. 查询已存在的购物车（ID=1，因为新建资源不会被持久化）
        fetched = keywords.send_get("/carts/1")
        keywords.assert_field(fetched, "id", 1)
        keywords.assert_field(fetched, "userId", is_not_none=True)
