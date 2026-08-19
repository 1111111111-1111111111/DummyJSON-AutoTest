"""
API 基类

所有模块 API 的公共基类，提供通用的 CRUD 操作封装。
"""
import allure
from src.core.http_client import HttpClient
from src.core.logger import logger
from src.core.config_manager import config


class BaseAPI:
    """
    API 基类

    封通 CRUD 操作，子类通过 resource_name 指定资源路径。
    """

    def __init__(self, client: HttpClient = None, resource_name: str = ""):
        """
        初始化 API 基类。

        Args:
            client: HTTP客户端实例
            resource_name: 资源名称（如 products, users）
        """
        self.client = client or HttpClient()
        self.resource_name = resource_name

    @allure.step("获取资源列表")
    def get_all(self, params: dict = None) -> dict:
        """
        获取资源列表。

        Args:
            params: 查询参数 (limit, skip, select, sortBy, order)

        Returns:
            分页响应数据
        """
        logger.info(f"GET /{self.resource_name} params={params}")
        response = self.client.get(f"/{self.resource_name}", params=params)
        return response.json()

    @allure.step("获取单个资源: id={resource_id}")
    def get_by_id(self, resource_id: int) -> dict:
        """
        获取单个资源。

        Args:
            resource_id: 资源ID

        Returns:
            资源详情
        """
        logger.info(f"GET /{self.resource_name}/{resource_id}")
        response = self.client.get(f"/{self.resource_name}/{resource_id}")
        return response.json()

    @allure.step("搜索资源: q={query}")
    def search(self, query: str) -> dict:
        """
        搜索资源。

        Args:
            query: 搜索关键词

        Returns:
            搜索结果
        """
        logger.info(f"GET /{self.resource_name}/search?q={query}")
        response = self.client.get(f"/{self.resource_name}/search", params={"q": query})
        return response.json()

    @allure.step("添加新资源")
    def add(self, data: dict) -> dict:
        """
        添加新资源。

        Args:
            data: 资源数据

        Returns:
            创建的资源
        """
        logger.info(f"POST /{self.resource_name}/add")
        response = self.client.post(f"/{self.resource_name}/add", json=data)
        return response.json()

    @allure.step("更新资源: id={resource_id} method={method}")
    def update(self, resource_id: int, data: dict, method: str = "PUT") -> dict:
        """
        更新资源。

        Args:
            resource_id: 资源ID
            data: 更新数据
            method: HTTP方法 (PUT/PATCH)

        Returns:
            更新后的资源
        """
        logger.info(f"{method} /{self.resource_name}/{resource_id}")
        if method.upper() == "PATCH":
            response = self.client.patch(f"/{self.resource_name}/{resource_id}", json=data)
        else:
            response = self.client.put(f"/{self.resource_name}/{resource_id}", json=data)
        return response.json()

    @allure.step("删除资源: id={resource_id}")
    def delete(self, resource_id: int) -> dict:
        """
        删除资源。

        Args:
            resource_id: 资源ID

        Returns:
            删除确认信息
        """
        logger.info(f"DELETE /{self.resource_name}/{resource_id}")
        response = self.client.delete(f"/{self.resource_name}/{resource_id}")
        return response.json()

    @allure.step("分页获取资源: limit={limit} skip={skip}")
    def get_paginated(self, limit: int = 10, skip: int = 0, select: str = None) -> dict:
        """
        分页获取资源。

        Args:
            limit: 每页数量
            skip: 跳过数量
            select: 选择字段（逗号分隔）

        Returns:
            分页数据
        """
        params = {"limit": limit, "skip": skip}
        if select:
            params["select"] = select
        return self.get_all(params=params)

    @allure.step("排序获取资源: sortBy={sort_by} order={order}")
    def get_sorted(self, sort_by: str, order: str = "asc") -> dict:
        """
        排序获取资源。

        Args:
            sort_by: 排序字段
            order: 排序方向 (asc/desc)

        Returns:
            排序后的数据
        """
        return self.get_all(params={"sortBy": sort_by, "order": order})
