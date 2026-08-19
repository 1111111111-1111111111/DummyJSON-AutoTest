# ============================================================
# Dockerfile — DummyJSON API 自动化测试项目（多阶段构建优化版）
# ============================================================
#
# 优化点：
#   1. 多阶段构建（builder + runtime），减少最终镜像体积
#   2. 依赖缓存层分离：requirements.txt 独立复制，未变更时复用缓存
#   3. 可选 WebDriver Manager + Chrome 安装层（用于未来 UI 测试扩展）
#   4. OCI 标准镜像标签（labels）
#   5. 健康检查（healthcheck）
#   6. Allure CLI 内置，支持容器内生成报告
#
# 构建命令：
#   docker build -t dummyjson-api-testing .
#   docker build --build-arg INSTALL_WEBDRIVER=true -t dummyjson-api-testing:full .
#
# 运行示例：
#   docker run --rm -e TEST_MODE=all dummyjson-api-testing
#   docker run --rm -e TEST_MODE=smoke -v $(pwd)/reports:/app/reports dummyjson-api-testing
# ============================================================

# ------------------------------------------------------------
# Stage 1: Builder — 安装 Python 依赖（利用层缓存）
# ------------------------------------------------------------
FROM python:3.11-slim AS builder

# 构建参数
ARG ALLURE_VERSION=2.27.0
ARG INSTALL_WEBDRIVER=false

# 环境变量：优化 Python 运行
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装编译依赖（某些 Python 包需要 gcc）
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境（隔离依赖，便于多阶段复制）
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 先复制依赖清单（利用 Docker 层缓存：依赖不变时跳过安装）
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

# ------------------------------------------------------------
# Stage 2: Runtime — 最终运行镜像
# ------------------------------------------------------------
FROM python:3.11-slim AS runtime

# 构建参数
ARG ALLURE_VERSION=2.27.0
ARG INSTALL_WEBDRIVER=false
ARG TEST_MODE=all

# 环境变量
ENV TEST_MODE=${TEST_MODE} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# OCI 标准镜像标签
LABEL org.opencontainers.image.title="DummyJSON API Testing" \
      org.opencontainers.image.description="API 自动化测试镜像（Pytest + Allure）" \
      org.opencontainers.image.source="https://github.com/${GITHUB_REPOSITORY:-dummyjson-api-testing}" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${ALLURE_VERSION}" \
      org.opencontainers.image.created="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      maintainer="CI/CD Pipeline"

# 安装运行时系统依赖：
#   - default-jre-headless：Allure CLI 运行依赖 Java
#   - curl/wget：下载工具
#   - jq：CI/CD 中 JSON 处理
#   - fonts-wqy-zenhei：中文字体（截图工具 PNG 渲染需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-jre-headless \
        curl \
        wget \
        jq \
        fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制虚拟环境（已安装所有 Python 依赖）
COPY --from=builder /opt/venv /opt/venv

# 安装 Allure CLI（固定版本，便于复现）
# 使用 .tgz 格式（体积更小）
RUN wget -q -O /tmp/allure.tgz \
        "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" \
    && mkdir -p /opt/allure \
    && tar -xzf /tmp/allure.tgz -C /opt/allure --strip-components=1 \
    && ln -s /opt/allure/bin/allure /usr/local/bin/allure \
    && rm /tmp/allure.tgz \
    && allure --version

# ------------------------------------------------------------
# 可选层：WebDriver Manager + Chrome（用于未来 UI 测试扩展）
# 通过 --build-arg INSTALL_WEBDRIVER=true 启用
# 当前项目为纯 API 测试，此层默认不安装以减小镜像体积
# ------------------------------------------------------------
RUN if [ "$INSTALL_WEBDRIVER" = "true" ]; then \
        echo ">>> 安装 Chrome 和 WebDriver Manager（UI 测试扩展）..." && \
        apt-get update && apt-get install -y --no-install-recommends \
            chromium \
            chromium-driver \
            unzip \
        && rm -rf /var/lib/apt/lists/* \
        && pip install webdriver-manager selenium \
        && echo ">>> Chrome + WebDriver Manager 安装完成" \
        && chromium --version; \
    else \
        echo ">>> INSTALL_WEBDRIVER=false，跳过 Chrome 安装（纯 API 测试模式）"; \
    fi

# 设置工作目录
WORKDIR /app

# 复制项目源码（.dockerignore 已排除不需要的文件）
COPY . .

# 复制入口脚本并赋予执行权限
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 预创建结果与日志目录
RUN mkdir -p reports/allure-results reports/allure-report logs screenshots

# 健康检查：验证 Python 环境和 Allure 可用
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import pytest; import allure; import requests" || exit 1

# 通过入口脚本读取 TEST_MODE 环境变量动态选择测试模式
# 支持：smoke / regression / all（默认 all）
ENTRYPOINT ["/docker-entrypoint.sh"]

# ------------------------------------------------------------
# Docker run 示例：
#   docker run --rm -e TEST_MODE=all dummyjson-api-testing
#   docker run --rm -e TEST_MODE=smoke dummyjson-api-testing
#   docker run --rm -e TEST_MODE=regression dummyjson-api-testing
#   docker run --rm -v $(pwd)/reports:/app/reports -e TEST_MODE=all dummyjson-api-testing
#
# 构建 UI 测试镜像（含 Chrome）：
#   docker build --build-arg INSTALL_WEBDRIVER=true -t dummyjson-api-testing:full .
#
# CI/CD 中使用 Buildx 缓存：
#   docker buildx build --cache-from type=gha --cache-to type=gha,mode=max .
# ------------------------------------------------------------
