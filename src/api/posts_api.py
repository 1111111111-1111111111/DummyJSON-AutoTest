"""Posts 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class PostsAPI(BaseAPI):
    """Posts 模块 API，处理帖子CRUD、搜索、标签等。"""

    def __init__(self, client=None):
        super().__init__(client, "posts")

    @allure.step("获取所有帖子标签")
    def get_tags(self) -> list:
        """获取所有帖子标签（含slug和name）。"""
        response = self.client.get("/posts/tags")
        return response.json()

    @allure.step("获取帖子标签列表")
    def get_tag_list(self) -> list:
        """获取帖子标签slug列表。"""
        response = self.client.get("/posts/tag-list")
        return response.json()

    @allure.step("按标签获取帖子: tag={tag}")
    def get_by_tag(self, tag: str) -> dict:
        """按标签获取帖子。"""
        response = self.client.get(f"/posts/tag/{tag}")
        return response.json()

    @allure.step("获取用户帖子: user_id={user_id}")
    def get_by_user(self, user_id: int) -> dict:
        """获取指定用户的帖子。"""
        response = self.client.get(f"/posts/user/{user_id}")
        return response.json()

    @allure.step("获取帖子评论: post_id={post_id}")
    def get_post_comments(self, post_id: int) -> dict:
        """获取指定帖子的评论。"""
        response = self.client.get(f"/posts/{post_id}/comments")
        return response.json()
