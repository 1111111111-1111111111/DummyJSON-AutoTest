"""
Posts 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Posts 模块")
@pytest.mark.smoke
class TestPostsSmoke:
    """Posts 模块冒烟测试用例。"""

    @allure.story("获取帖子列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取帖子列表应返回分页数据")
    def test_get_all_posts(self, posts_api):
        """验证获取帖子列表返回分页结构。"""
        data = posts_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "posts")

    @allure.story("获取单个帖子")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取单个帖子应返回正确帖子")
    def test_get_single_post(self, posts_api):
        """验证获取单个帖子返回正确的帖子信息。"""
        post = posts_api.get_by_id(1)
        
        Assertions.assert_field_equals(post, "id", 1)
        Assertions.assert_field_not_none(post, "title")
        Assertions.assert_field_not_none(post, "body")
