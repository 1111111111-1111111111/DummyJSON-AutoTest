"""
数据驱动加载器

支持从 YAML、JSON、Excel 文件读取测试数据，
统一返回列表格式供 pytest 参数化使用。
"""
import json
import os
from pathlib import Path

import yaml
import openpyxl

from src.core.logger import logger

# 测试数据根目录
TESTDATA_DIR = Path(__file__).resolve().parent.parent.parent / "testdata"


class DataLoader:
    """
    数据驱动加载器

    支持从 YAML、JSON、Excel 文件加载测试数据。
    """

    @staticmethod
    def load_yaml(file_path: str) -> list:
        """
        从 YAML 文件加载测试数据。

        Args:
            file_path: 相对于 testdata/ 的文件路径，或绝对路径

        Returns:
            测试数据列表
        """
        full_path = DataLoader._resolve_path(file_path, ".yaml")
        with open(full_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.debug(f"YAML 数据加载完成: {full_path} | 条数={len(data) if isinstance(data, list) else 1}")
        return data if isinstance(data, list) else [data]

    @staticmethod
    def load_json(file_path: str) -> list:
        """
        从 JSON 文件加载测试数据。

        Args:
            file_path: 相对于 testdata/ 的文件路径，或绝对路径

        Returns:
            测试数据列表
        """
        full_path = DataLoader._resolve_path(file_path, ".json")
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"JSON 数据加载完成: {full_path} | 条数={len(data) if isinstance(data, list) else 1}")
        return data if isinstance(data, list) else [data]

    @staticmethod
    def load_excel(file_path: str, sheet_name: str = None) -> list:
        """
        从 Excel 文件加载测试数据。

        Args:
            file_path: 相对于 testdata/ 的文件路径，或绝对路径
            sheet_name: 工作表名称，默认取第一个

        Returns:
            测试数据列表（每行一个字典，键为表头）
        """
        full_path = DataLoader._resolve_path(file_path, ".xlsx")
        wb = openpyxl.load_workbook(full_path, data_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []

        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
        data = []
        for row in rows[1:]:
            if all(cell is None for cell in row):
                continue
            row_data = {}
            for i, val in enumerate(row):
                row_data[headers[i]] = val
            data.append(row_data)

        wb.close()
        logger.debug(f"Excel 数据加载完成: {full_path} | sheet={sheet_name} | 条数={len(data)}")
        return data

    @staticmethod
    def load(file_path: str, **kwargs) -> list:
        """
        根据文件扩展名自动选择加载器。

        Args:
            file_path: 文件路径
            **kwargs: 额外参数（如 sheet_name）

        Returns:
            测试数据列表
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".yaml", ".yml"):
            return DataLoader.load_yaml(file_path)
        elif ext == ".json":
            return DataLoader.load_json(file_path)
        elif ext == ".xlsx":
            return DataLoader.load_excel(file_path, **kwargs.get("sheet_name"))
        else:
            raise ValueError(f"不支持的数据文件格式: {ext}")

    @staticmethod
    def _resolve_path(file_path: str, ext: str) -> Path:
        """解析文件路径，支持相对路径和绝对路径。"""
        p = Path(file_path)
        if not p.is_absolute():
            p = TESTDATA_DIR / file_path
        if not p.exists() and not p.suffix:
            p = p.with_suffix(ext)
        if not p.exists():
            raise FileNotFoundError(f"测试数据文件不存在: {p}")
        return p
