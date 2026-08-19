"""
日志管理模块

提供统一的日志记录功能，支持控制台和文件输出，
日志级别分为 DEBUG/INFO/WARNING/ERROR/CRITICAL。
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class LoggerManager:
    """日志管理器，负责创建和配置logger实例。"""

    _loggers = {}

    @staticmethod
    def get_logger(name: str = "dummyjson_test") -> logging.Logger:
        """
        获取或创建logger实例。

        Args:
            name: logger名称，默认为 dummyjson_test

        Returns:
            logging.Logger: 配置好的logger实例
        """
        if name in LoggerManager._loggers:
            return LoggerManager._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if logger.handlers:
            return logger

        # 日志格式
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(fmt)

        # 文件handler（按大小轮转）
        log_file = os.path.join(LOG_DIR, f"test_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        LoggerManager._loggers[name] = logger
        return logger


# 全局logger实例
logger = LoggerManager.get_logger()
