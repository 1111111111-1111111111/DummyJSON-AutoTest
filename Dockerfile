# ============================================================
# DummyJSON API 自动化测试 — 精简生产级 Dockerfile
# ============================================================
# 核心原则：
#   1. 单阶段构建（简化维护，减少层数）
#   2. 依赖缓存层分离（requirements.txt 变更才重建）
#   3. Allure CLI 内置（支持容器内生成报告）
#   4. 健康检查 + 入口点脚本（灵活执行）
#   5. 无冗余包（移除 Chrome/WebDriver，纯 API 测试）
# ============================================================
FROM python:3.11-slim

# 构建参数
ARG ALLURE_VERSION=2.27.0

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai

# OCI 镜像标签
LABEL org.opencontainers.image.title="DummyJSON API Testing" \
      org.opencontainers.image.description="API 自动化测试镜像（Pytest + Allure）" \
      org.opencontainers.image.licenses="MIT"

# 安装运行时依赖：Java（Allure 依赖）+ 常用工具
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-jre-headless \
        curl \
        wget \
        jq \
        tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# --------- 安装 Python 依赖（利用 Docker 层缓存） ---------
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# --------- 安装 Allure CLI ---------
RUN for url in \
        "https://maven.aliyun.com/repository/central/io/qameta/allure/allure-commandline/${ALLURE_VERSION}/allure-commandline-${ALLURE_VERSION}.tgz" \
        "https://repo1.maven.org/maven2/io/qameta/allure/allure-commandline/${ALLURE_VERSION}/allure-commandline-${ALLURE_VERSION}.tgz" \
        "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" \
    ; do \
        echo ">>> 尝试下载 Allure: ${url}" && \
        wget -q --tries=3 --timeout=60 -O /tmp/allure.tgz "${url}" && break || echo ">>> 下载失败，尝试下一个源"; \
    done && \
    tar -xzf /tmp/allure.tgz -C /opt/ && \
    ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/local/bin/allure && \
    rm /tmp/allure.tgz

# --------- 复制项目代码 ---------
COPY . .

# 预创建目录
RUN mkdir -p reports/allure-results reports/allure-report logs screenshots

# 确保入口点脚本存在且可执行
RUN if [ ! -f /app/docker-entrypoint.sh ]; then \
        echo '#!/bin/bash' > /app/docker-entrypoint.sh && \
        echo 'set -e' >> /app/docker-entrypoint.sh && \
        echo 'echo "========================================="' >> /app/docker-entrypoint.sh && \
        echo 'echo "DummyJSON API 测试容器"' >> /app/docker-entrypoint.sh && \
        echo 'echo "测试模式: ${TEST_MODE:-smoke}"' >> /app/docker-entrypoint.sh && \
        echo 'echo "========================================="' >> /app/docker-entrypoint.sh && \
        echo 'pytest -v --alluredir=reports/allure-results "$@" || EXIT_CODE=$?' >> /app/docker-entrypoint.sh && \
        echo 'allure generate reports/allure-results -o reports/allure-report --clean' >> /app/docker-entrypoint.sh && \
        echo 'exit $EXIT_CODE' >> /app/docker-entrypoint.sh && \
        chmod +x /app/docker-entrypoint.sh; \
    fi

# 入口点脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import pytest; import allure" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]