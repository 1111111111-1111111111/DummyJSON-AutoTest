"""辅助函数模块 - 提供通用的工具函数。"""
import time
import random
import string
from src.core.logger import logger


def generate_random_string(length: int = 10) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def wait(seconds: float):
    logger.debug(f"等待 {seconds}s")
    time.sleep(seconds)

def get_random_id(min_val: int = 1, max_val: int = 100) -> int:
    return random.randint(min_val, max_val)

def safe_json_parse(response):
    try:
        return response.json()
    except Exception as e:
        logger.warning(f"JSON解析失败: {e}")
        return {}
