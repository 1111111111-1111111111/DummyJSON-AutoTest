"""
Products 模块回归测试

覆盖 Products 模块所有接口的正向、异常、边界、数据驱动场景。
"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator
from src.core.data_loader import DataLoader
from src.core.data_generator import data_generator


@allure.epic("DummyJSON API")
@allure.feature("Products 模块")
@pytest.mark.regression
class TestProductsRegression:
    """Products 模块全量回归测试用例。"""

    @allure.story("获取商品列表")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取商品列表并验证Schema")
    def test_get_all_products_schema(self, products_api):
        """验证获取商品列表的Schema正确性。"""
        data = products_api.get_all()

        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "products")
        for product in data["products"]:
            SchemaValidator.validate_response(product, "product")

    @allure.story("获取单个商品")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取ID为1的商品")
    def test_get_product_by_id(self, products_api):
        """验证获取单个商品的详细信息。"""
        product = products_api.get_by_id(1)

        Assertions.assert_field_equals(product, "id", 1)
        Assertions.assert_field_not_none(product, "title")
        Assertions.assert_field_not_none(product, "price")
        Assertions.assert_field_not_none(product, "category")
        Assertions.assert_field_not_none(product, "description")
        SchemaValidator.validate_response(product, "product")

    @allure.story("搜索商品")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("搜索关键词phone")
    def test_search_products(self, products_api):
        """验证搜索商品功能。"""
        data = products_api.search("phone")

        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "products")

    @allure.story("获取分类列表")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取商品分类列表")
    def test_get_categories(self, products_api):
        """验证获取商品分类列表。"""
        categories = products_api.get_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        for cat in categories:
            assert "slug" in cat
            assert "name" in cat

    @allure.story("获取分类slug列表")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取商品分类slug列表")
    def test_get_category_list(self, products_api):
        """验证获取商品分类slug列表。"""
        category_list = products_api.get_category_list()

        assert isinstance(category_list, list)
        assert len(category_list) > 0
        assert "beauty" in category_list

    @allure.story("按分类获取商品")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按smartphones分类获取商品")
    def test_get_by_category(self, products_api):
        """验证按分类获取商品。"""
        data = products_api.get_by_category("smartphones")

        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "products")
        for product in data["products"]:
            assert product["category"] == "smartphones"

    @allure.story("分页获取商品")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("分页参数 limit=5 skip=0")
    def test_pagination(self, products_api):
        """验证商品分页参数。"""
        data = products_api.get_paginated(limit=5, skip=0)

        Assertions.assert_field_equals(data, "limit", 5)
        Assertions.assert_field_equals(data, "skip", 0)
        assert len(data["products"]) == 5

    @allure.story("排序获取商品")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按price升序排序")
    def test_sort_by_price(self, products_api):
        """验证商品排序功能。"""
        data = products_api.get_sorted("price", "asc")

        Assertions.assert_list_not_empty(data, "products")
        prices = [p["price"] for p in data["products"]]
        assert prices == sorted(prices), "价格应升序排列"

    @allure.story("选择字段")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("仅选择title和price字段")
    def test_select_fields(self, products_api):
        """验证选择特定字段功能。"""
        data = products_api.get_paginated(limit=5, skip=0, select="title,price")

        Assertions.assert_list_not_empty(data, "products")
        for product in data["products"]:
            assert "title" in product
            assert "price" in product

    @allure.story("添加商品")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("添加新产品")
    def test_add_product(self, products_api, gen):
        """验证添加新商品功能。"""
        new_product = gen.generate_product()
        result = products_api.add(new_product)

        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "title", new_product["title"])
        Assertions.assert_field_equals(result, "price", new_product["price"])

    @allure.story("添加商品-最小数据")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("仅传title添加产品")
    def test_add_product_minimal(self, products_api):
        """验证仅传title添加商品。"""
        result = products_api.add({"title": "Minimal Test Product"})

        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "title", "Minimal Test Product")

    @allure.story("更新商品")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("PUT更新商品")
    def test_update_product_put(self, products_api):
        """验证PUT更新商品功能。"""
        result = products_api.update(1, {"title": "Updated Product Title"}, method="PUT")

        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "title", "Updated Product Title")

    @allure.story("部分更新商品")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("PATCH部分更新商品")
    def test_update_product_patch(self, products_api):
        """验证PATCH部分更新商品功能。"""
        result = products_api.update(1, {"price": 999.99}, method="PATCH")

        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "price", 999.99)

    @allure.story("删除商品")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("删除商品")
    def test_delete_product(self, products_api):
        """验证删除商品功能。"""
        result = products_api.delete(1)

        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("异常场景")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("查询不存在的产品ID返回404")
    def test_product_not_found(self, products_api):
        """验证查询不存在的产品ID返回404。"""
        response = products_api.client.get("/products/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("JSON数据驱动")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("JSON数据驱动 - {test_id}")
    @pytest.mark.parametrize("case", DataLoader.load_json("products/product_data.json"))
    def test_product_json_data_driven(self, products_api, case):
        """使用JSON数据驱动测试产品场景。"""
        if "data" in case:
            result = products_api.add(case["data"])
            Assertions.assert_field_not_none(result, "id")
        elif "query" in case:
            data = products_api.search(case["query"])
            Assertions.assert_list_not_empty(data, "products")

    @allure.story("关键字驱动: 完整CRUD流程")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("关键字组合 - 添加+查询+更新+删除")
    def test_keyword_crud_flow(self, keywords, gen):
        """使用关键字组合完成完整CRUD流程。

        注意: DummyJSON 的 POST 是模拟操作，不会真正持久化数据，
        因此 GET/PUT/DELETE 步骤使用已存在的资源ID=1进行验证。
        """
        # 1. 添加产品（验证POST返回id和传入字段）
        product = gen.generate_product()
        created = keywords.send_post("/products/add", product)
        product_id = keywords.extract_field(created, "id")
        assert product_id is not None
        keywords.assert_field(created, "title", product["title"])

        # 2. 查询已存在的产品（ID=1，因为新建资源不会被持久化）
        fetched = keywords.send_get("/products/1")
        keywords.assert_field(fetched, "id", 1)
        keywords.assert_field(fetched, "title", is_not_none=True)

        # 3. 更新已存在的产品
        updated = keywords.send_put("/products/1", {"title": "Updated Title"})
        keywords.assert_field(updated, "title", "Updated Title")

        # 4. 删除已存在的产品
        deleted = keywords.send_delete("/products/1")
        keywords.assert_field(deleted, "isDeleted", True)

    @allure.story("边界场景")
    @allure.severity(allure.severity_level.MINOR)
    @allure.title("limit=0获取全部商品")
    def test_limit_zero(self, products_api):
        """验证limit=0获取所有商品。

        注意: DummyJSON 在 limit=0 时返回全部数据，且响应中的 limit 字段
        返回的是总数而非0，因此只验证返回的数据量大于默认分页大小。
        """
        data = products_api.get_all(params={"limit": 0})

        assert data["total"] > 30  # 应返回全部商品
        assert len(data["products"]) > 30  # 返回的商品数量应超过默认分页
