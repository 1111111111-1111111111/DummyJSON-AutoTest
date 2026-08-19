"""
JSON Schema 校验器

使用 jsonschema 库验证 API 响应是否符合预定义的 JSON Schema。
"""
import jsonschema
from src.core.logger import logger


class SchemaValidator:
    """
    JSON Schema 校验器
    """

    @staticmethod
    def validate(data: dict, schema: dict) -> bool:
        """
        校验数据是否符合 JSON Schema。

        Args:
            data: 待校验的数据
            schema: JSON Schema 定义

        Returns:
            bool: 校验通过返回 True

        Raises:
            jsonschema.ValidationError: 校验失败时抛出
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            logger.debug("JSON Schema 校验通过")
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"JSON Schema 校验失败: {e.message} | 路径: {list(e.absolute_path)}")
            raise
        except jsonschema.SchemaError as e:
            logger.error(f"JSON Schema 定义有误: {e.message}")
            raise

    @staticmethod
    def validate_response(response_data: dict, resource_type: str = "product") -> bool:
        """
        校验单个资源对象的通用字段。

        Args:
            response_data: API 响应数据
            resource_type: 资源类型 (product/user/post/comment/quote/recipe/todo/cart)

        Returns:
            bool: 校验通过返回 True
        """
        schemas = {
            "product": {
                "type": "object",
                "required": ["id", "title", "price"],
                "properties": {
                    "id": {"type": "number"},
                    "title": {"type": "string"},
                    "price": {"type": "number"},
                },
            },
            "user": {
                "type": "object",
                "required": ["id", "firstName", "lastName"],
                "properties": {
                    "id": {"type": "number"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                },
            },
            "post": {
                "type": "object",
                "required": ["id", "title", "body"],
                "properties": {
                    "id": {"type": "number"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
            "comment": {
                "type": "object",
                "required": ["id", "body", "postId"],
                "properties": {
                    "id": {"type": "number"},
                    "body": {"type": "string"},
                    "postId": {"type": "number"},
                },
            },
            "quote": {
                "type": "object",
                "required": ["id", "quote", "author"],
                "properties": {
                    "id": {"type": "number"},
                    "quote": {"type": "string"},
                    "author": {"type": "string"},
                },
            },
            "recipe": {
                "type": "object",
                "required": ["id", "name", "ingredients"],
                "properties": {
                    "id": {"type": "number"},
                    "name": {"type": "string"},
                    "ingredients": {"type": "array"},
                },
            },
            "todo": {
                "type": "object",
                "required": ["id", "todo", "completed"],
                "properties": {
                    "id": {"type": "number"},
                    "todo": {"type": "string"},
                    "completed": {"type": "boolean"},
                },
            },
            "cart": {
                "type": "object",
                "required": ["id", "products", "userId"],
                "properties": {
                    "id": {"type": "number"},
                    "products": {"type": "array"},
                    "userId": {"type": "number"},
                },
            },
            "auth_login": {
                "type": "object",
                "required": ["id", "username", "accessToken", "refreshToken"],
                "properties": {
                    "id": {"type": "number"},
                    "username": {"type": "string"},
                    "accessToken": {"type": "string"},
                    "refreshToken": {"type": "string"},
                },
            },
            "paginated": {
                "type": "object",
                "required": ["total", "skip", "limit"],
                "properties": {
                    "total": {"type": "number"},
                    "skip": {"type": "number"},
                    "limit": {"type": "number"},
                },
            },
        }

        schema = schemas.get(resource_type)
        if not schema:
            raise ValueError(f"不支持的资源类型: {resource_type}")
        return SchemaValidator.validate(data=response_data, schema=schema)
