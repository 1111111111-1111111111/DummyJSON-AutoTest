"""Users 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Users 模块")
@pytest.mark.regression
class TestUsersRegression:
    """Users 模块全量回归测试用例。"""

    @allure.story("获取用户列表")
    @allure.title("获取用户列表并验证Schema")
    def test_get_all_users_schema(self, users_api):
        data = users_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "users")
        for user in data["users"]:
            SchemaValidator.validate_response(user, "user")

    @allure.story("获取单个用户")
    @allure.title("获取ID为1的用户")
    def test_get_user_by_id(self, users_api):
        user = users_api.get_by_id(1)
        Assertions.assert_field_equals(user, "id", 1)
        Assertions.assert_field_not_none(user, "firstName")
        Assertions.assert_field_not_none(user, "email")

    @allure.story("搜索用户")
    @allure.title("搜索关键词John")
    def test_search_users(self, users_api):
        data = users_api.search("John")
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "users")

    @allure.story("过滤用户")
    @allure.title("过滤hair.color=Brown")
    def test_filter_users_hair(self, users_api):
        data = users_api.filter_users("hair.color", "Brown")
        Assertions.assert_list_not_empty(data, "users")
        for user in data["users"]:
            assert user["hair"]["color"] == "Brown"

    @allure.story("过滤用户-性别")
    @allure.title("过滤gender=female")
    def test_filter_users_gender(self, users_api):
        data = users_api.filter_users("gender", "female")
        Assertions.assert_list_not_empty(data, "users")
        for user in data["users"]:
            assert user["gender"] == "female"

    @allure.story("获取用户购物车")
    @allure.title("获取用户1的购物车")
    def test_get_user_carts(self, users_api):
        data = users_api.get_user_carts(1)
        Assertions.assert_list_not_empty(data, "carts")

    @allure.story("获取用户帖子")
    @allure.title("获取用户5的帖子")
    def test_get_user_posts(self, users_api):
        data = users_api.get_user_posts(5)
        Assertions.assert_list_not_empty(data, "posts")

    @allure.story("获取用户待办")
    @allure.title("获取用户1的待办")
    def test_get_user_todos(self, users_api):
        """验证获取用户待办列表。"""
        data = users_api.get_user_todos(1)
        Assertions.assert_list_not_empty(data, "todos")

    @allure.story("添加用户")
    @allure.title("添加新用户")
    def test_add_user(self, users_api, gen):
        new_user = gen.generate_user()
        result = users_api.add(new_user)
        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "firstName", new_user["firstName"])

    @allure.story("更新用户")
    @allure.title("PUT更新用户")
    def test_update_user_put(self, users_api):
        result = users_api.update(1, {"lastName": "Updated"}, method="PUT")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "lastName", "Updated")

    @allure.story("部分更新用户")
    @allure.title("PATCH部分更新用户")
    def test_update_user_patch(self, users_api):
        result = users_api.update(1, {"age": 30}, method="PATCH")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "age", 30)

    @allure.story("删除用户")
    @allure.title("删除用户")
    def test_delete_user(self, users_api):
        result = users_api.delete(1)
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("分页")
    @allure.title("分页获取用户")
    def test_pagination(self, users_api):
        data = users_api.get_paginated(limit=5, skip=5)
        Assertions.assert_field_equals(data, "limit", 5)
        Assertions.assert_field_equals(data, "skip", 5)

    @allure.story("排序")
    @allure.title("按firstName排序用户")
    def test_sort_by_firstname(self, users_api):
        data = users_api.get_sorted("firstName", "asc")
        Assertions.assert_list_not_empty(data, "users")

    @allure.story("选择字段")
    @allure.title("仅选择firstName和age字段")
    def test_select_fields(self, users_api):
        data = users_api.get_paginated(limit=5, skip=0, select="firstName,age")
        Assertions.assert_list_not_empty(data, "users")
        for user in data["users"]:
            assert "firstName" in user
            assert "age" in user

    @allure.story("异常场景")
    @allure.title("查询不存在的用户ID返回404")
    def test_user_not_found(self, users_api):
        response = users_api.client.get("/users/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("关键字驱动: 用户CRUD流程")
    @allure.title("关键字组合 - 添加+查询+更新+删除用户")
    def test_keyword_user_crud(self, keywords, gen):
        """使用关键字组合完成用户CRUD流程。

        注意: DummyJSON 的 POST 是模拟操作，不会真正持久化数据，
        因此 GET/PUT/DELETE 步骤使用已存在的用户ID=1进行验证。
        """
        # 1. 添加用户（验证POST返回id和firstName）
        user = gen.generate_user()
        created = keywords.send_post("/users/add", user)
        user_id = keywords.extract_field(created, "id")
        assert user_id is not None
        keywords.assert_field(created, "firstName", user["firstName"])

        # 2. 查询已存在的用户（ID=1）
        fetched = keywords.send_get("/users/1")
        keywords.assert_field(fetched, "id", 1)
        keywords.assert_field(fetched, "firstName", is_not_none=True)

        # 3. 更新已存在的用户
        updated = keywords.send_put("/users/1", {"firstName": "UpdatedName"})
        keywords.assert_field(updated, "firstName", "UpdatedName")

        # 4. 删除已存在的用户
        deleted = keywords.send_delete("/users/1")
        keywords.assert_field(deleted, "isDeleted", True)
