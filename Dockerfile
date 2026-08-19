# ============================================================
# Dockerfile — DummyJSON API 自动化测试项目
# 用途：在容器内运行 Pytest 全量测试（冒烟 + 回归），
#       并生成 Allure 测试报告，适配 CI/CD 流水线。
# ============================================================

# 基础镜像：Python 3.11 精简版
FROM python:3.11-slim AS base

# 声明构建参数，CI 中可通过 --build-arg 注入
ARG TEST_MODE=all
ENV TEST_MODE=${TEST_MODE} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖：
#   - default-jre-headless：Allure CLI 运行依赖 Java
#   - curl/unzip：下载并解压 Allure 分发包
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-jre-headless \
        curl \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# 安装 Allure CLI（固定版本，便于复现）
ARG ALLURE_VERSION=2.27.0
RUN curl -sSL -o /tmp/allure.zip \
        "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.zip" \
    && unzip -q /tmp/allure.zip -d /opt/ \
    && ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/local/bin/allure \
    && rm /tmp/allure.zip \
    && allure --version

# 设置工作目录
WORKDIR /app

# 先复制依赖清单，利用 Docker 层缓存（依赖不变时跳过安装）
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制项目源码
COPY . .

# 复制入口脚本并赋予执行权限
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 预创建结果与日志目录
RUN mkdir -p reports/allure-results reports/allure-report logs

# 通过入口脚本读取 TEST_MODE 环境变量动态选择测试模式
# 支持：smoke / regression / all（默认 all）
ENTRYPOINT ["/docker-entrypoint.sh"]

# Docker run 示例：
#   docker run --rm -e TEST_MODE=all dummyjson-api-testing          # 全量（冒烟+回归）
#   docker run --rm -e TEST_MODE=smoke dummyjson-api-testing        # 仅冒烟
#   docker run --rm -e TEST_MODE=regression dummyjson-api-testing   # 仅回归
#   docker run --rm -v $(pwd)/reports:/app/reports -e TEST_MODE=all dummyjson-api-testing  # 报告挂载到宿主机
