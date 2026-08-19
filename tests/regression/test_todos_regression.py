"""Todos 模块回归测试 - 覆盖所有接口及边界场景。"""
import pytest
import allure
from src.utils.assertions import Assertions
from src.core.schema_validator import SchemaValidator


@allure.epic("DummyJSON API")
@allure.feature("Todos 模块")
@pytest.mark.regression
class TestTodosRegression:
    """Todos 模块全量回归测试用例。"""

    @allure.story("获取待办列表")
    @allure.title("获取待办列表并验证Schema")
    def test_get_all_todos_schema(self, todos_api):
        data = todos_api.get_all()
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "todos")
        for todo in data["todos"]:
            SchemaValidator.validate_response(todo, "todo")

    @allure.story("获取单个待办")
    @allure.title("获取ID为1的待办")
    def test_get_todo_by_id(self, todos_api):
        todo = todos_api.get_by_id(1)
        Assertions.assert_field_equals(todo, "id", 1)
        Assertions.assert_field_not_none(todo, "todo")
        Assertions.assert_field_in(todo, "completed")

    @allure.story("获取随机待办")
    @allure.title("获取随机待办应返回有效数据")
    def test_get_random_todo(self, todos_api):
        todo = todos_api.get_random()
        Assertions.assert_field_not_none(todo, "id")
        Assertions.assert_field_not_none(todo, "todo")
        Assertions.assert_field_in(todo, "completed")

    @allure.story("获取用户待办")
    @allure.title("获取用户1的待办")
    def test_get_by_user(self, todos_api):
        """验证获取用户待办列表。"""
        data = todos_api.get_by_user(1)
        Assertions.assert_list_not_empty(data, "todos")
        for todo in data["todos"]:
            assert todo["userId"] == 1

    @allure.story("添加待办")
    @allure.title("添加新待办")
    def test_add_todo(self, todos_api, gen):
        new_todo = gen.generate_todo(user_id=5)
        result = todos_api.add(new_todo)
        Assertions.assert_field_not_none(result, "id")
        Assertions.assert_field_equals(result, "todo", new_todo["todo"])

    @allure.story("更新待办")
    @allure.title("PUT更新待办")
    def test_update_todo_put(self, todos_api):
        result = todos_api.update(1, {"completed": False}, method="PUT")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "completed", False)

    @allure.story("部分更新待办")
    @allure.title("PATCH部分更新待办")
    def test_update_todo_patch(self, todos_api):
        result = todos_api.update(1, {"completed": True}, method="PATCH")
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "completed", True)

    @allure.story("删除待办")
    @allure.title("删除待办")
    def test_delete_todo(self, todos_api):
        result = todos_api.delete(1)
        Assertions.assert_field_equals(result, "id", 1)
        Assertions.assert_field_equals(result, "isDeleted", True)

    @allure.story("分页")
    @allure.title("分页获取待办")
    def test_pagination(self, todos_api):
        data = todos_api.get_paginated(limit=5, skip=10)
        Assertions.assert_field_equals(data, "limit", 5)
        Assertions.assert_field_equals(data, "skip", 10)

    @allure.story("选择字段")
    @allure.title("仅选择todo和completed字段")
    def test_select_fields(self, todos_api):
        data = todos_api.get_paginated(limit=5, skip=0, select="todo,completed")
        Assertions.assert_list_not_empty(data, "todos")
        for todo in data["todos"]:
            assert "todo" in todo

    @allure.story("异常场景")
    @allure.title("查询不存在的待办ID返回404")
    def test_todo_not_found(self, todos_api):
        response = todos_api.client.get("/todos/99999")
        Assertions.assert_status_code(response, 404)

    @allure.story("关键字驱动: 待办CRUD流程")
    @allure.title("关键字组合 - 添加+查询+更新+删除待办")
    def test_keyword_todo_crud(self, keywords, gen):
        """使用关键字组合完成待办CRUD流程。

        注意: DummyJSON 的 POST 是模拟操作，不会真正持久化数据，
        因此 GET/PUT/DELETE 步骤使用已存在的待办ID=1进行验证。
        """
        # 1. 添加待办（验证POST返回id和todo）
        todo = gen.generate_todo(user_id=1)
        created = keywords.send_post("/todos/add", todo)
        todo_id = keywords.extract_field(created, "id")
        assert todo_id is not None
        keywords.assert_field(created, "todo", todo["todo"])

        # 2. 查询已存在的待办（ID=1）
        fetched = keywords.send_get("/todos/1")
        keywords.assert_field(fetched, "id", 1)
        keywords.assert_field(fetched, "todo", is_not_none=True)

        # 3. 更新已存在的待办
        updated = keywords.send_put("/todos/1", {"completed": True})
        keywords.assert_field(updated, "completed", True)

        # 4. 删除已存在的待办
        deleted = keywords.send_delete("/todos/1")
        keywords.assert_field(deleted, "isDeleted", True)
