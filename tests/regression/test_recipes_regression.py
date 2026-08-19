"""Recipes 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Recipes 模块")
@pytest.mark.regression
class TestRecipesRegression:
    """Recipes 模块全量回归测试用例。"""

    @allure.story("获取食谱列表")
    @allure.title("获取食谱列表并验证Schema")
    def test_get_all_recipes_schema(self, recipes_api):
        data = recipes_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "recipes")
        for recipe in data["recipes"]:
            SchemaValidator.validate_response(recipe, "recipe")

    @allure.story("获取单个食谱")
    @allure.title("获取ID为1的食谱")
    def test_get_recipe_by_id(self, recipes_api):
        recipe = recipes_api.get_by_id(1)
        Assertions.assert_field_equals(recipe, "id", 1)
        Assertions.assert_field_not_none(recipe, "name")
        Assertions.assert_field_not_none(recipe, "ingredients")

    @allure.story("搜索食谱")
    @allure.title("搜索关键词Margherita")
    def test_search_recipes(self, recipes_api):
        data = recipes_api.search("Margherita")
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "recipes")

    @allure.story("获取食谱标签")
    @allure.title("获取所有食谱标签")
    def test_get_tags(self, recipes_api):
        tags = recipes_api.get_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0

    @allure.story("按标签获取食谱")
    @allure.title("按Pakistani标签获取食谱")
    def test_get_by_tag(self, recipes_api):
        data = recipes_api.get_by_tag("Pakistani")
        Assertions.assert_list_not_empty(data, "recipes")

    @allure.story("按餐类获取食谱")
    @allure.title("按Snack餐类获取食谱")
    def test_get_by_meal_type(self, recipes_api):
        data = recipes_api.get_by_meal_type("Snack")
        Assertions.assert_list_not_empty(data, "recipes")

    @allure.story("添加食谱")
    @allure.title("添加新食谱")
    def test_add_recipe(self, recipes_api, gen):
        new_recipe = gen.generate_recipe()
        result = recipes_api.add(new_recipe)
        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "name", new_recipe["name"])

    @allure.story("更新食谱")
    @allure.title("PUT更新食谱")
    def test_update_recipe_put(self, recipes_api):
        result = recipes_api.update(1, {"name": "Updated Recipe Name"}, method="PUT")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "name", "Updated Recipe Name")

    @allure.story("部分更新食谱")
    @allure.title("PATCH部分更新食谱")
    def test_update_recipe_patch(self, recipes_api):
        result = recipes_api.update(1, {"difficulty": "Hard"}, method="PATCH")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "difficulty", "Hard")

    @allure.story("删除食谱")
    @allure.title("删除食谱")
    def test_delete_recipe(self, recipes_api):
        result = recipes_api.delete(1)
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("分页")
    @allure.title("分页获取食谱")
    def test_pagination(self, recipes_api):
        data = recipes_api.get_paginated(limit=5, skip=0)
        Assertions.assert_field_equals(data, "limit", 5)
        assert len(data["recipes"]) == 5

    @allure.story("排序")
    @allure.title("按name排序食谱")
    def test_sort_by_name(self, recipes_api):
        data = recipes_api.get_sorted("name", "asc")
        Assertions.assert_list_not_empty(data, "recipes")

    @allure.story("选择字段")
    @allure.title("仅选择name和image字段")
    def test_select_fields(self, recipes_api):
        data = recipes_api.get_paginated(limit=5, skip=0, select="name,image")
        Assertions.assert_list_not_empty(data, "recipes")
        for recipe in data["recipes"]:
            assert "name" in recipe

    @allure.story("异常场景")
    @allure.title("查询不存在的食谱ID返回404")
    def test_recipe_not_found(self, recipes_api):
        response = recipes_api.client.get("/recipes/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("关键字驱动: 食谱查询流程")
    @allure.title("关键字组合 - 获取+搜索+按标签")
    def test_keyword_recipe_flow(self, keywords):
        all_recipes = keywords.send_get("/recipes")
        keywords.assert_pagination(all_recipes)

        searched = keywords.send_get("/recipes/search", params={"q": "Pizza"})
        keywords.assert_has_list(searched, "recipes")

        by_tag = keywords.send_get("/recipes/tag/Pizza")
        keywords.assert_has_list(by_tag, "recipes")
