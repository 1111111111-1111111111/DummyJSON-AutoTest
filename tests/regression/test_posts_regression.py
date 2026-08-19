"""Posts 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Posts 模块")
@pytest.mark.regression
class TestPostsRegression:
    """Posts 模块全量回归测试用例。"""

    @allure.story("获取帖子列表")
    @allure.title("获取帖子列表并验证Schema")
    def test_get_all_posts_schema(self, posts_api):
        data = posts_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "posts")
        for post in data["posts"]:
            SchemaValidator.validate_response(post, "post")

    @allure.story("获取单个帖子")
    @allure.title("获取ID为1的帖子")
    def test_get_post_by_id(self, posts_api):
        post = posts_api.get_by_id(1)
        Assertions.assert_field_equals(post, "id", 1)
        Assertions.assert_field_not_none(post, "title")
        Assertions.assert_field_not_none(post, "body")

    @allure.story("搜索帖子")
    @allure.title("搜索关键词love")
    def test_search_posts(self, posts_api):
        data = posts_api.search("love")
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "posts")

    @allure.story("获取帖子标签")
    @allure.title("获取所有帖子标签")
    def test_get_tags(self, posts_api):
        tags = posts_api.get_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0
        for tag in tags:
            assert "slug" in tag
            assert "name" in tag

    @allure.story("获取标签列表")
    @allure.title("获取帖子标签slug列表")
    def test_get_tag_list(self, posts_api):
        tag_list = posts_api.get_tag_list()
        assert isinstance(tag_list, list)
        assert len(tag_list) > 0

    @allure.story("按标签获取帖子")
    @allure.title("按life标签获取帖子")
    def test_get_by_tag(self, posts_api):
        data = posts_api.get_by_tag("life")
        Assertions.assert_list_not_empty(data, "posts")

    @allure.story("获取用户帖子")
    @allure.title("获取用户5的帖子")
    def test_get_by_user(self, posts_api):
        data = posts_api.get_by_user(5)
        Assertions.assert_list_not_empty(data, "posts")

    @allure.story("获取帖子评论")
    @allure.title("获取帖子1的评论")
    def test_get_post_comments(self, posts_api):
        data = posts_api.get_post_comments(1)
        Assertions.assert_list_not_empty(data, "comments")

    @allure.story("添加帖子")
    @allure.title("添加新帖子")
    def test_add_post(self, posts_api, gen):
        new_post = gen.generate_post(user_id=1)
        result = posts_api.add(new_post)
        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "userId", 1)

    @allure.story("更新帖子")
    @allure.title("PUT更新帖子")
    def test_update_post_put(self, posts_api):
        result = posts_api.update(1, {"title": "Updated Post Title"}, method="PUT")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "title", "Updated Post Title")

    @allure.story("部分更新帖子")
    @allure.title("PATCH部分更新帖子")
    def test_update_post_patch(self, posts_api):
        result = posts_api.update(1, {"body": "Updated body content"}, method="PATCH")
        Assertions.assert_field_equals(result, "id", 1)

    @allure.story("删除帖子")
    @allure.title("删除帖子")
    def test_delete_post(self, posts_api):
        result = posts_api.delete(1)
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("分页")
    @allure.title("分页获取帖子")
    def test_pagination(self, posts_api):
        data = posts_api.get_paginated(limit=5, skip=0)
        Assertions.assert_field_equals(data, "limit", 5)
        assert len(data["posts"]) == 5

    @allure.story("排序")
    @allure.title("按title排序帖子")
    def test_sort_by_title(self, posts_api):
        data = posts_api.get_sorted("title", "asc")
        Assertions.assert_list_not_empty(data, "posts")

    @allure.story("选择字段")
    @allure.title("仅选择title和reactions字段")
    def test_select_fields(self, posts_api):
        data = posts_api.get_paginated(limit=5, skip=0, select="title,reactions,userId")
        Assertions.assert_list_not_empty(data, "posts")
        for post in data["posts"]:
            assert "title" in post

    @allure.story("异常场景")
    @allure.title("查询不存在的帖子ID返回404")
    def test_post_not_found(self, posts_api):
        response = posts_api.client.get("/posts/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("关键字驱动: 帖子CRUD流程")
    @allure.title("关键字组合 - 添加+查询+更新+删除帖子")
    def test_keyword_post_crud(self, keywords, gen):
        """使用关键字组合完成帖子CRUD流程。

        注意: DummyJSON 的 POST 是模拟操作，不会真正持久化数据，
        因此 GET/PUT/DELETE 步骤使用已存在的帖子ID=1进行验证。
        """
        # 1. 添加帖子（验证POST返回id和title）
        post = gen.generate_post(user_id=1)
        created = keywords.send_post("/posts/add", post)
        post_id = keywords.extract_field(created, "id")
        assert post_id is not None
        keywords.assert_field(created, "title", post["title"])

        # 2. 查询已存在的帖子（ID=1）
        fetched = keywords.send_get("/posts/1")
        keywords.assert_field(fetched, "id", 1)
        keywords.assert_field(fetched, "title", is_not_none=True)

        # 3. 更新已存在的帖子
        updated = keywords.send_put("/posts/1", {"title": "Updated"})
        keywords.assert_field(updated, "title", "Updated")

        # 4. 删除已存在的帖子
        deleted = keywords.send_delete("/posts/1")
        keywords.assert_field(deleted, "isDeleted", True)
