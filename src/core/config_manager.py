"""
配置管理模块

支持从 .env、config.yaml、config.json 多种格式读取配置，
支持多环境切换（dev/staging/prod）。
"""
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.core.logger import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 配置文件目录
CONFIG_DIR = PROJECT_ROOT / "config"


class ConfigManager:
    """
    配置管理器

    按优先级合并配置：.env < config.yaml < config.json < 环境变量覆盖。
    支持通过环境变量 ENV 切换 dev/staging/prod 配置段。
    """

    _instance = None
    _config = {}

    def __new__(cls):
        """单例模式，确保全局只有一个配置实例。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        """加载所有配置源并合并。"""
        # 1. 加载 .env 文件
        env_file = CONFIG_DIR / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.debug(f"已加载 .env 配置: {env_file}")

        # 2. 加载 config.yaml
        yaml_file = CONFIG_DIR / "config.yaml"
        yaml_config = {}
        if yaml_file.exists():
            with open(yaml_file, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
            logger.debug(f"已加载 YAML 配置: {yaml_file}")

        # 3. 加载 config.json
        json_file = CONFIG_DIR / "config.json"
        json_config = {}
        if json_file.exists():
            with open(json_file, "r", encoding="utf-8") as f:
                json_config = json.load(f)
            logger.debug(f"已加载 JSON 配置: {json_file}")

        # 4. 确定当前环境
        self._env = os.getenv("ENV", yaml_config.get("env", "dev"))
        logger.info(f"当前运行环境: {self._env}")

        # 5. 合并配置：yaml 全局段 + yaml 环境段 + json 全局段 + json 环境段
        merged = {}
        merged.update(yaml_config.get("global", {}))
        merged.update(yaml_config.get(self._env, {}))
        merged.update(json_config.get("global", {}))
        merged.update(json_config.get(self._env, {}))

        # 6. 环境变量覆盖（优先级最高）
        for key, val in os.environ.items():
            if key.startswith("APP_"):
                config_key = key[4:].lower()
                merged[config_key] = val

        self._config = merged
        logger.debug(f"最终合并配置: {self._config}")

    def get(self, key: str, default=None):
        """
        获取配置项。

        Args:
            key: 配置键名，支持点号分隔（如 'http.timeout'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    @property
    def env(self) -> str:
        """返回当前环境名称。"""
        return self._env

    @property
    def base_url(self) -> str:
        """返回API基础URL。"""
        return self.get("base_url", "https://dummyjson.com")

    @property
    def http_timeout(self) -> int:
        """返回HTTP超时时间（秒）。"""
        return int(self.get("timeout", 30))

    @property
    def http_retry(self) -> int:
        """返回HTTP重试次数。"""
        return int(self.get("retry_count", 3))

    @property
    def auth_credentials(self) -> dict:
        """返回认证凭据。"""
        return self.get("auth", {"username": "emilys", "password": "emilyspass"})


# 全局配置实例
config = ConfigManager()
