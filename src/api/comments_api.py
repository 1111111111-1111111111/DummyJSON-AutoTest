"""Comments 模块 API 封装"""
import allure
from src.api.base_api import BaseAPI


class CommentsAPI(BaseAPI):
    """Comments 模块 API，处理评论CRUD。"""

    def __init__(self, client=None):
        super().__init__(client, "comments")

    @allure.step("按帖子获取评论: post_id={post_id}")
    def get_by_post(self, post_id: int) -> dict:
        """获取指定帖子的评论。"""
        response = self.client.get(f"/comments/post/{post_id}")
        return response.json()
