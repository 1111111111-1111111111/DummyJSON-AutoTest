"""
Recipes 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Recipes 模块")
@pytest.mark.smoke
class TestRecipesSmoke:
    """Recipes 模块冒烟测试用例。"""

    @allure.story("获取食谱列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取食谱列表应返回分页数据")
    def test_get_all_recipes(self, recipes_api):
        """验证获取食谱列表返回分页结构。"""
        data = recipes_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "recipes")

    @allure.story("获取单个食谱")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取单个食谱应返回正确食谱")
    def test_get_single_recipe(self, recipes_api):
        """验证获取单个食谱返回正确的食谱信息。"""
        recipe = recipes_api.get_by_id(1)
        
        Assertions.assert_field_equals(recipe, "id", 1)
        Assertions.assert_field_not_none(recipe, "name")
        Assertions.assert_field_not_none(recipe, "ingredients")
