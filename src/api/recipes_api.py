"""Recipes 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class RecipesAPI(BaseAPI):
    """Recipes 模块 API，处理食谱CRUD、搜索、标签等。"""

    def __init__(self, client=None):
        super().__init__(client, "recipes")

    @allure.step("获取所有食谱标签")
    def get_tags(self) -> list:
        """获取所有食谱标签。"""
        response = self.client.get("/recipes/tags")
        return response.json()

    @allure.step("按标签获取食谱: tag={tag}")
    def get_by_tag(self, tag: str) -> dict:
        """按标签获取食谱。"""
        response = self.client.get(f"/recipes/tag/{tag}")
        return response.json()

    @allure.step("按餐类获取食谱: meal_type={meal_type}")
    def get_by_meal_type(self, meal_type: str) -> dict:
        """按餐类获取食谱。"""
        response = self.client.get(f"/recipes/meal-type/{meal_type}")
        return response.json()
