"""Products 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class ProductsAPI(BaseAPI):
    """Products 模块 API，处理商品CRUD、搜索、分类等。"""

    def __init__(self, client=None):
        super().__init__(client, "products")

    @allure.step("获取所有商品分类")
    def get_categories(self) -> list:
        """获取所有商品分类（含slug和name）。"""
        response = self.client.get("/products/categories")
        return response.json()

    @allure.step("获取商品分类列表")
    def get_category_list(self) -> list:
        """获取商品分类slug列表。"""
        response = self.client.get("/products/category-list")
        return response.json()

    @allure.step("按分类获取商品: category={category}")
    def get_by_category(self, category: str) -> dict:
        """按分类获取商品。"""
        response = self.client.get(f"/products/category/{category}")
        return response.json()
