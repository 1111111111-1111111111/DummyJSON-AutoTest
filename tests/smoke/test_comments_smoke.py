"""
Comments 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Comments 模块")
@pytest.mark.smoke
class TestCommentsSmoke:
    """Comments 模块冒烟测试用例。"""

    @allure.story("获取评论列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取评论列表应返回分页数据")
    def test_get_all_comments(self, comments_api):
        """验证获取评论列表返回分页结构。"""
        data = comments_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "comments")

    @allure.story("获取单个评论")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取单个评论应返回正确评论")
    def test_get_single_comment(self, comments_api):
        """验证获取单个评论返回正确的评论信息。"""
        comment = comments_api.get_by_id(1)
        
        Assertions.assert_field_equals(comment, "id", 1)
        Assertions.assert_field_not_none(comment, "body")
        Assertions.assert_field_not_none(comment, "postId")
