"""Comments 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Comments 模块")
@pytest.mark.regression
class TestCommentsRegression:
    """Comments 模块全量回归测试用例。"""

    @allure.story("获取评论列表")
    @allure.title("获取评论列表并验证Schema")
    def test_get_all_comments_schema(self, comments_api):
        data = comments_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "comments")
        for comment in data["comments"]:
            SchemaValidator.validate_response(comment, "comment")

    @allure.story("获取单个评论")
    @allure.title("获取ID为1的评论")
    def test_get_comment_by_id(self, comments_api):
        comment = comments_api.get_by_id(1)
        Assertions.assert_field_equals(comment, "id", 1)
        Assertions.assert_field_not_none(comment, "body")
        Assertions.assert_field_not_none(comment, "postId")

    @allure.story("按帖子获取评论")
    @allure.title("获取帖子6的评论")
    def test_get_by_post(self, comments_api):
        data = comments_api.get_by_post(6)
        Assertions.assert_list_not_empty(data, "comments")
        for comment in data["comments"]:
            assert comment["postId"] == 6

    @allure.story("添加评论")
    @allure.title("添加新评论")
    def test_add_comment(self, comments_api, gen):
        new_comment = gen.generate_comment(post_id=3, user_id=5)
        result = comments_api.add(new_comment)
        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "body", new_comment["body"])

    @allure.story("更新评论")
    @allure.title("PUT更新评论")
    def test_update_comment_put(self, comments_api):
        result = comments_api.update(1, {"body": "Updated comment body"}, method="PUT")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "body", "Updated comment body")

    @allure.story("部分更新评论")
    @allure.title("PATCH部分更新评论")
    def test_update_comment_patch(self, comments_api):
        result = comments_api.update(1, {"body": "Patched body"}, method="PATCH")
        Assertions.assert_field_equals(result, "id", 1)

    @allure.story("删除评论")
    @allure.title("删除评论")
    def test_delete_comment(self, comments_api):
        result = comments_api.delete(1)
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("分页")
    @allure.title("分页获取评论")
    def test_pagination(self, comments_api):
        data = comments_api.get_paginated(limit=5, skip=10)
        Assertions.assert_field_equals(data, "limit", 5)
        Assertions.assert_field_equals(data, "skip", 10)

    @allure.story("选择字段")
    @allure.title("仅选择body和postId字段")
    def test_select_fields(self, comments_api):
        data = comments_api.get_paginated(limit=5, skip=0, select="body,postId")
        Assertions.assert_list_not_empty(data, "comments")
        for comment in data["comments"]:
            assert "body" in comment

    @allure.story("异常场景")
    @allure.title("查询不存在的评论ID返回404")
    def test_comment_not_found(self, comments_api):
        response = comments_api.client.get("/comments/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("关键字驱动: 评论CRUD流程")
    @allure.title("关键字组合 - 添加+查询+更新+删除评论")
    def test_keyword_comment_crud(self, keywords, gen):
        """使用关键字组合完成评论CRUD流程。

        注意: DummyJSON 的 POST 是模拟操作，不会真正持久化数据，
        因此 GET/PUT/DELETE 步骤使用已存在的评论ID=1进行验证。
        """
        # 1. 添加评论（验证POST返回id和body）
        comment = gen.generate_comment(post_id=1, user_id=1)
        created = keywords.send_post("/comments/add", comment)
        comment_id = keywords.extract_field(created, "id")
        assert comment_id is not None
        keywords.assert_field(created, "body", comment["body"])

        # 2. 查询已存在的评论（ID=1）
        fetched = keywords.send_get("/comments/1")
        keywords.assert_field(fetched, "id", 1)
        keywords.assert_field(fetched, "body", is_not_none=True)

        # 3. 更新已存在的评论
        updated = keywords.send_put("/comments/1", {"body": "Updated"})
        keywords.assert_field(updated, "body", "Updated")

        # 4. 删除已存在的评论
        deleted = keywords.send_delete("/comments/1")
        keywords.assert_field(deleted, "isDeleted", True)
