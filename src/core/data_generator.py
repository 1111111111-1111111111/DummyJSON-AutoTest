"""
数据生成器

使用 Faker 库生成随机测试数据，
用于创建产品、用户等资源的请求体。
"""
import random
import string

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

from src.core.logger import logger


class DataGenerator:
    """
    测试数据生成器

    使用 Faker 生成随机化测试数据，支持产品、用户、帖子等。
    """

    def __init__(self):
        """初始化数据生成器。"""
        if FAKER_AVAILABLE:
            self.faker = Faker("zh_CN")
        else:
            self.faker = None
            logger.warning("Faker 库未安装，将使用简单随机数据")

    def generate_product(self) -> dict:
        """生成随机产品数据。"""
        if self.faker:
            data = {
                "title": f"Test Product {self.faker.word().title()}",
                "description": self.faker.sentence(nb_words=15),
                "category": random.choice(["beauty", "fragrances", "furniture", "groceries", "laptops"]),
                "price": round(random.uniform(10.0, 999.99), 2),
                "discountPercentage": round(random.uniform(0, 30), 2),
                "rating": round(random.uniform(3.0, 5.0), 2),
                "stock": random.randint(1, 100),
                "tags": [self.faker.word() for _ in range(3)],
                "brand": self.faker.company(),
                "sku": "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            }
        else:
            data = {
                "title": f"Test Product {''.join(random.choices(string.ascii_letters, k=6))}",
                "description": "A test product for automated testing",
                "category": "beauty",
                "price": round(random.uniform(10.0, 999.99), 2),
                "discountPercentage": round(random.uniform(0, 30), 2),
                "rating": round(random.uniform(3.0, 5.0), 2),
                "stock": random.randint(1, 100),
                "tags": ["test", "automated", "quality"],
                "brand": "TestBrand",
                "sku": "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            }
        logger.debug(f"生成产品数据: {data['title']}")
        return data

    def generate_user(self) -> dict:
        """生成随机用户数据。"""
        if self.faker:
            data = {
                "firstName": self.faker.first_name(),
                "lastName": self.faker.last_name(),
                "age": random.randint(18, 80),
                "gender": random.choice(["male", "female"]),
                "email": self.faker.email(),
                "phone": self.faker.phone_number(),
                "username": self.faker.user_name(),
                "password": self.faker.password(length=12),
                "birthDate": self.faker.date_of_birth().strftime("%Y-%m-%d"),
                "bloodGroup": random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
                "height": round(random.uniform(150.0, 200.0), 2),
                "weight": round(random.uniform(40.0, 120.0), 2),
                "eyeColor": random.choice(["Brown", "Blue", "Green", "Gray"]),
            }
        else:
            data = {
                "firstName": "TestUser",
                "lastName": "Automated",
                "age": random.randint(18, 80),
                "gender": random.choice(["male", "female"]),
                "email": f"test{random.randint(1000,9999)}@example.com",
                "phone": f"+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                "username": f"testuser{random.randint(1000,9999)}",
                "password": "TestPass123!",
                "birthDate": "1990-01-01",
                "bloodGroup": "O+",
                "height": 175.0,
                "weight": 70.0,
                "eyeColor": "Brown",
            }
        logger.debug(f"生成用户数据: {data['firstName']} {data['lastName']}")
        return data

    def generate_post(self, user_id: int = 1) -> dict:
        """生成随机帖子数据。"""
        if self.faker:
            data = {
                "title": self.faker.sentence(nb_words=8),
                "body": self.faker.paragraph(nb_sentences=5),
                "userId": user_id,
                "tags": [self.faker.word() for _ in range(3)],
                "reactions": {"likes": random.randint(0, 500), "dislikes": random.randint(0, 50)},
            }
        else:
            data = {
                "title": f"Test Post {random.randint(1000,9999)}",
                "body": "This is a test post body for automated testing purposes.",
                "userId": user_id,
                "tags": ["test", "automated"],
                "reactions": {"likes": random.randint(0, 500), "dislikes": random.randint(0, 50)},
            }
        logger.debug(f"生成帖子数据: userId={user_id}")
        return data

    def generate_comment(self, post_id: int = 1, user_id: int = 1) -> dict:
        """生成随机评论数据。"""
        if self.faker:
            data = {
                "body": self.faker.sentence(nb_words=12),
                "postId": post_id,
                "userId": user_id,
            }
        else:
            data = {
                "body": f"Test comment {random.randint(1000,9999)}",
                "postId": post_id,
                "userId": user_id,
            }
        logger.debug(f"生成评论数据: postId={post_id}, userId={user_id}")
        return data

    def generate_todo(self, user_id: int = 1) -> dict:
        """生成随机待办事项数据。"""
        if self.faker:
            data = {
                "todo": self.faker.sentence(nb_words=6),
                "completed": random.choice([True, False]),
                "userId": user_id,
            }
        else:
            data = {
                "todo": f"Test todo item {random.randint(1000,9999)}",
                "completed": random.choice([True, False]),
                "userId": user_id,
            }
        logger.debug(f"生成待办数据: userId={user_id}")
        return data

    def generate_cart(self, user_id: int = 1) -> dict:
        """生成随机购物车数据。"""
        products = []
        for _ in range(random.randint(1, 5)):
            products.append({
                "id": random.randint(1, 194),
                "quantity": random.randint(1, 10),
            })
        data = {
            "userId": user_id,
            "products": products,
        }
        logger.debug(f"生成购物车数据: userId={user_id}, products={len(products)}")
        return data

    def generate_recipe(self) -> dict:
        """生成随机食谱数据。"""
        if self.faker:
            data = {
                "name": f"{self.faker.word().title()} Special Recipe",
                "ingredients": [self.faker.word() for _ in range(random.randint(3, 8))],
                "instructions": [self.faker.sentence() for _ in range(random.randint(3, 6))],
                "prepTimeMinutes": random.randint(5, 60),
                "cookTimeMinutes": random.randint(10, 90),
                "servings": random.randint(1, 8),
                "difficulty": random.choice(["Easy", "Medium", "Hard"]),
                "cuisine": random.choice(["Italian", "Asian", "American", "French", "Indian"]),
                "caloriesPerServing": random.randint(100, 800),
                "tags": [self.faker.word() for _ in range(3)],
                "userId": random.randint(1, 208),
                "mealType": [random.choice(["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"])],
            }
        else:
            data = {
                "name": f"Test Recipe {random.randint(1000,9999)}",
                "ingredients": ["flour", "sugar", "salt", "water"],
                "instructions": ["Mix ingredients", "Cook for 30 minutes", "Serve hot"],
                "prepTimeMinutes": 15,
                "cookTimeMinutes": 30,
                "servings": 4,
                "difficulty": "Easy",
                "cuisine": "Italian",
                "caloriesPerServing": 300,
                "tags": ["test", "easy"],
                "userId": 1,
                "mealType": ["Dinner"],
            }
        logger.debug(f"生成食谱数据: {data['name']}")
        return data


# 全局数据生成器实例
data_generator = DataGenerator()
