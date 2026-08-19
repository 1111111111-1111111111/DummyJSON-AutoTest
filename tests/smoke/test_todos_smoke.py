"""
Todos 模块冒烟测试
"""
import pytest
import allure
from src.utils.assertions import Assertions


@allure.epic("DummyJSON API")
@allure.feature("Todos 模块")
@pytest.mark.smoke
class TestTodosSmoke:
    """Todos 模块冒烟测试用例。"""

    @allure.story("获取待办列表")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("获取待办列表应返回分页数据")
    def test_get_all_todos(self, todos_api):
        """验证获取待办列表返回分页结构。"""
        data = todos_api.get_all()
        
        Assertions.assert_pagination_fields(data)
        Assertions.assert_list_not_empty(data, "todos")

    @allure.story("获取随机待办")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取随机待办应返回有效数据")
    def test_get_random_todo(self, todos_api):
        """验证获取随机待办返回有效的待办数据。"""
        todo = todos_api.get_random()
        
        Assertions.assert_field_not_none(todo, "id")
        Assertions.assert_field_not_none(todo, "todo")
        Assertions.assert_field_in(todo, "completed")
