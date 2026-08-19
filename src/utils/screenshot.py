"""
断言失败截图工具

当测试用例断言失败时，自动留存失败现场证据：
  1. HTML 格式截图（格式化的证据报告，可在浏览器中打开查看）
  2. JSON 格式证据（结构化数据，可供程序解析）
  3. PNG 格式截图（纯图片，依赖 Pillow，可选）

证据内容包含：
  - 测试用例名称、时间戳
  - 断言错误类型与错误消息
  - 异常堆栈追踪
  - 最近的 HTTP 请求上下文（method/url/params/body/headers）
  - 最近的 HTTP 响应上下文（status_code/headers/body/elapsed）
"""
import os
import json as json_module
import traceback as tb_module
from datetime import datetime
from pathlib import Path

import allure

from src.core.logger import logger

# Pillow 是可选依赖：未安装时 PNG 截图自动跳过
try:
    from PIL import Image, ImageDraw, ImageFont
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False


class ScreenshotUtil:
    """断言失败截图工具。"""

    # 截图输出目录
    SCREENSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "screenshots"

    # ---- 配色方案 ----
    COLOR_FAILURE_RED = "#dc3545"
    COLOR_FAILURE_BG = "#fde8ea"
    COLOR_HEADER_BG = "#1a1a2e"
    COLOR_REQ_BG = "#e8f4fd"
    COLOR_RES_BG = "#fef5e7"
    COLOR_CODE_BG = "#f8f9fa"

    @classmethod
    def capture_failure(
        cls,
        test_name: str,
        error_info: Exception,
        request_context: dict = None,
        response_context: dict = None,
    ) -> dict:
        """
        捕获断言失败现场，生成截图证据文件。

        Args:
            test_name: 测试用例名称（如 test_login_valid_credentials）
            error_info: 异常对象（通常是 AssertionError）
            request_context: 请求上下文字典
            response_context: 响应上下文字典

        Returns:
            dict: 各格式截图文件路径 {"html": ..., "json": ..., "png": ...}
        """
        cls.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        timestamp_display = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # 清理文件名中的非法字符
        safe_name = "".join(
            c if c.isalnum() or c in "_-" else "_" for c in test_name
        ).strip("_")
        file_base = f"{timestamp_str}_{safe_name}"

        # 构建证据数据
        evidence = {
            "test_name": test_name,
            "timestamp": timestamp_display,
            "error_type": type(error_info).__name__,
            "error_message": str(error_info),
            "traceback": tb_module.format_exc(),
            "request": cls._safe_dict(request_context),
            "response": cls._safe_dict(response_context),
        }

        file_paths = {}

        # 1. 保存 JSON 证据
        json_path = cls.SCREENSHOT_DIR / f"{file_base}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json_module.dump(evidence, f, ensure_ascii=False, indent=2)
        file_paths["json"] = str(json_path)

        # 2. 保存 HTML 截图
        html_path = cls.SCREENSHOT_DIR / f"{file_base}.html"
        html_content = cls._build_html(evidence)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        file_paths["html"] = str(html_path)

        # 3. 尝试生成 PNG 截图（需要 Pillow）
        png_path = cls._render_png(evidence, file_base)
        if png_path:
            file_paths["png"] = str(png_path)

        # 4. 附加到 Allure 报告
        cls._attach_allure(evidence, html_content, png_path)

        logger.error(
            f"[截图工具] 断言失败证据已留存:\n"
            f"  HTML: {html_path}\n"
            f"  JSON: {json_path}"
            + (f"\n  PNG:  {png_path}" if png_path else "")
        )

        return file_paths

    @classmethod
    def _build_html(cls, evidence: dict) -> str:
        """构建格式化的 HTML 证据报告。"""

        def _fmt_json(obj):
            if obj is None:
                return '<span style="color:#999">（无数据）</span>'
            try:
                return (
                    f'<pre style="background:{cls.COLOR_CODE_BG};padding:12px;'
                    f'border-radius:6px;overflow-x:auto;font-size:13px;'
                    f'line-height:1.6;">{json_module.dumps(obj, ensure_ascii=False, indent=2)}</pre>'
                )
            except (TypeError, ValueError):
                return f'<pre style="...">{str(obj)[:2000]}</pre>'

        req = evidence.get("request") or {}
        resp = evidence.get("response") or {}

        status_code = resp.get("status_code", "N/A")
        method = req.get("method", "N/A")
        url = req.get("url", "N/A")

        # 根据状态码着色
        if isinstance(status_code, int):
            if status_code < 300:
                status_color = "#28a745"
            elif status_code < 400:
                status_color = "#ffc107"
            else:
                status_color = "#dc3545"
        else:
            status_color = "#6c757d"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>断言失败截图 - {evidence['test_name']}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #f5f5f5; padding: 20px; }}
  .container {{ max-width: 960px; margin: 0 auto; background: #fff; border-radius: 12px;
               box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
  .header {{ background: {cls.COLOR_FAILURE_RED}; color: #fff; padding: 20px 28px; }}
  .header h1 {{ font-size: 22px; font-weight: 700; }}
  .header .sub {{ font-size: 14px; opacity: 0.9; margin-top: 6px; }}
  .section {{ padding: 18px 28px; border-bottom: 1px solid #eee; }}
  .section h2 {{ font-size: 16px; color: #333; margin-bottom: 10px;
               border-left: 4px solid {cls.COLOR_FAILURE_RED}; padding-left: 10px; }}
  .error-box {{ background: {cls.COLOR_FAILURE_BG}; border-left: 4px solid {cls.COLOR_FAILURE_RED};
               padding: 14px 16px; border-radius: 6px; }}
  .error-type {{ display: inline-block; background: {cls.COLOR_FAILURE_RED}; color: #fff;
               padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;
               margin-bottom: 8px; }}
  .error-msg {{ font-size: 14px; color: #333; line-height: 1.8; word-break: break-all; }}
  .traceback {{ background: {cls.COLOR_CODE_BG}; padding: 12px; border-radius: 6px;
               font-family: "Consolas", "Courier New", monospace; font-size: 12px;
               line-height: 1.6; overflow-x: auto; color: #555; white-space: pre-wrap;
               max-height: 300px; overflow-y: auto; }}
  .req-box {{ background: {cls.COLOR_REQ_BG}; border-radius: 8px; padding: 14px; }}
  .res-box {{ background: {cls.COLOR_RES_BG}; border-radius: 8px; padding: 14px; }}
  .status-badge {{ display: inline-block; padding: 3px 12px; border-radius: 4px;
                  font-weight: 700; font-size: 14px; color: #fff;
                  background: {status_color}; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .meta-item {{ font-size: 13px; }}
  .meta-label {{ color: #888; font-weight: 600; }}
  .meta-value {{ color: #333; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>&#9888; 断言失败截图 (Assertion Failed)</h1>
    <div class="sub">{evidence['timestamp']} | {evidence['test_name']}</div>
  </div>

  <div class="section">
    <h2>错误信息</h2>
    <div class="error-box">
      <span class="error-type">{evidence['error_type']}</span>
      <div class="error-msg">{cls._escape_html(evidence['error_message'])}</div>
    </div>
  </div>

  <div class="section">
    <h2>异常堆栈追踪</h2>
    <div class="traceback">{cls._escape_html(evidence.get('traceback', ''))}</div>
  </div>

  <div class="section">
    <h2>HTTP 请求上下文</h2>
    <div class="req-box">
      <div class="meta-grid" style="margin-bottom:12px;">
        <div class="meta-item"><span class="meta-label">Method:</span>
          <span class="meta-value">{method}</span></div>
        <div class="meta-item"><span class="meta-label">Status:</span>
          <span class="status-badge">{status_code}</span></div>
      </div>
      <div style="margin-bottom:8px;"><span class="meta-label">URL:</span>
        <span class="meta-value" style="word-break:break-all;">{url}</span></div>
      {_fmt_json(req)}
    </div>
  </div>

  <div class="section">
    <h2>HTTP 响应上下文</h2>
    <div class="res-box">
      {_fmt_json(resp)}
    </div>
  </div>

  <div class="section" style="border-bottom:none;">
    <span style="font-size:12px;color:#999;">由 ScreenshotUtil 自动生成 |
      {evidence['timestamp']}</span>
  </div>
</div>
</body>
</html>"""

    @classmethod
    def _render_png(cls, evidence: dict, file_base: str):
        """使用 Pillow 生成 PNG 截图（可选，Pillow 不可用时跳过）。"""
        if not _PILLOW_AVAILABLE:
            logger.debug("[截图工具] Pillow 未安装，跳过 PNG 生成")
            return None

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logger.debug("[截图工具] Pillow 未安装，跳过 PNG 生成")
            return None

        try:
            # 画布尺寸
            width = 1000
            # 根据内容动态计算高度
            req = evidence.get("request") or {}
            resp = evidence.get("response") or {}
            content_lines = [
                f"ERROR TYPE: {evidence['error_type']}",
                f"TEST: {evidence['test_name']}",
                f"TIME: {evidence['timestamp']}",
                "",
                "ERROR MESSAGE:",
                cls._truncate(str(evidence["error_message"]), 80),
                "",
                f"REQUEST: {req.get('method', '?')} {req.get('url', '?')}",
                f"RESPONSE STATUS: {resp.get('status_code', 'N/A')}",
                "",
                "TRACEBACK (last 5 lines):",
            ]
            tb_lines = (evidence.get("traceback") or "").strip().split("\n")[-5:]
            content_lines.extend(tb_lines)

            line_height = 24
            padding = 30
            header_height = 60
            height = header_height + len(content_lines) * line_height + padding * 2

            img = Image.new("RGB", (width, height), color=(245, 245, 245))
            draw = ImageDraw.Draw(img)

            # 加载字体（优先支持中文的字体，跨平台兼容）
            font, title_font = cls._load_fonts()

            # 绘制红色标题栏
            draw.rectangle([0, 0, width, header_height], fill=(220, 53, 69))
            draw.text(
                (padding, 18),
                "ASSERTION FAILED - Screenshot Evidence",
                fill=(255, 255, 255),
                font=title_font,
            )

            # 绘制内容
            y = header_height + padding
            for line in content_lines:
                color = (51, 51, 51)
                if line.startswith("ERROR"):
                    color = (220, 53, 69)
                elif "TRACEBACK" in line:
                    color = (100, 100, 100)
                elif line.startswith("REQUEST"):
                    color = (0, 102, 204)
                draw.text((padding, y), line, fill=color, font=font)
                y += line_height

            png_path = cls.SCREENSHOT_DIR / f"{file_base}.png"
            img.save(str(png_path), "PNG")
            logger.debug(f"[截图工具] PNG 截图已生成: {png_path}")
            return str(png_path)

        except Exception as e:
            logger.warning(f"[截图工具] PNG 生成失败: {e}")
            return None

    # 跨平台字体候选列表（按优先级尝试）
    _FONT_CANDIDATES = [
        # Windows 中文字体
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/Deng.ttf",
        "C:/Windows/Fonts/NotoSansSC-VF.ttf",
        # Linux 中文字体
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        # macOS 中文字体
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # 通用回退
        "C:/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "DejaVuSansMono.ttf",
    ]

    @classmethod
    def _load_fonts(cls):
        """加载支持中文的字体（按候选顺序回退）。"""
        content_font = None
        title_font = None

        for path in cls._FONT_CANDIDATES:
            try:
                content_font = ImageFont.truetype(path, 14)
                title_font = ImageFont.truetype(path, 20)
                logger.debug(f"[截图工具] 使用字体: {path}")
                return content_font, title_font
            except (OSError, IOError):
                continue

        # 全部失败则用默认字体（中文可能显示为方块）
        content_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        return content_font, title_font

    @classmethod
    def _attach_allure(cls, evidence: dict, html_content: str, png_path: str = None):
        """将截图证据附加到 Allure 报告。"""
        try:
            # JSON 附件
            allure.attach(
                json_module.dumps(evidence, ensure_ascii=False, indent=2),
                name="失败证据(JSON)",
                attachment_type=allure.attachment_type.JSON,
            )
            # HTML 附件
            allure.attach(
                html_content,
                name="失败截图(HTML)",
                attachment_type=allure.attachment_type.HTML,
            )
            # PNG 附件
            if png_path and os.path.exists(png_path):
                with open(png_path, "rb") as f:
                    allure.attach(
                        f.read(),
                        name="失败截图(PNG)",
                        attachment_type=allure.attachment_type.PNG,
                    )
        except Exception:
            pass

    @staticmethod
    def _safe_dict(data):
        """安全转换数据为可序列化的字典。"""
        if data is None:
            return None
        if isinstance(data, dict):
            return data
        try:
            return dict(data)
        except (TypeError, ValueError):
            return {"raw": str(data)[:2000]}

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义 HTML 特殊字符。"""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "<br>")
        )

    @staticmethod
    def _truncate(text: str, max_len: int = 80) -> str:
        """截断文本。"""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."
