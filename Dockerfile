# ============================================================
# DummyJSON API 自动化测试 — 精简生产级 Dockerfile
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

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-jre-headless \
        curl \
        wget \
        jq \
        tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# --------- 安装 Python 依赖 ---------
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

# --------- 创建入口点脚本（直接写入，避免文件不存在） ---------
RUN echo '#!/bin/bash' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# 默认值' >> /docker-entrypoint.sh && \
    echo 'TEST_MODE=${TEST_MODE:-"smoke"}' >> /docker-entrypoint.sh && \
    echo 'TEST_MARKER=${TEST_MARKER:-""}' >> /docker-entrypoint.sh && \
    echo 'EXIT_CODE=0' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo 'echo "========================================="' >> /docker-entrypoint.sh && \
    echo 'echo "DummyJSON API 测试容器"' >> /docker-entrypoint.sh && \
    echo 'echo "测试模式: ${TEST_MODE}"' >> /docker-entrypoint.sh && \
    echo '[ -n "$TEST_MARKER" ] && echo "测试标记: ${TEST_MARKER}"' >> /docker-entrypoint.sh && \
    echo 'echo "========================================="' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo 'case ${TEST_MODE} in' >> /docker-entrypoint.sh && \
    echo '  "smoke")' >> /docker-entrypoint.sh && \
    echo '    echo ">>> 执行冒烟测试"' >> /docker-entrypoint.sh && \
    echo '    pytest -v -m smoke --alluredir=reports/allure-results "$@" || EXIT_CODE=$?' >> /docker-entrypoint.sh && \
    echo '    ;;' >> /docker-entrypoint.sh && \
    echo '  "regression")' >> /docker-entrypoint.sh && \
    echo '    echo ">>> 执行回归测试"' >> /docker-entrypoint.sh && \
    echo '    pytest -v -m regression --alluredir=reports/allure-results "$@" || EXIT_CODE=$?' >> /docker-entrypoint.sh && \
    echo '    ;;' >> /docker-entrypoint.sh && \
    echo '  "all")' >> /docker-entrypoint.sh && \
    echo '    echo ">>> 执行全部测试"' >> /docker-entrypoint.sh && \
    echo '    pytest -v --alluredir=reports/allure-results "$@" || EXIT_CODE=$?' >> /docker-entrypoint.sh && \
    echo '    ;;' >> /docker-entrypoint.sh && \
    echo '  "custom")' >> /docker-entrypoint.sh && \
    echo '    echo ">>> 执行自定义测试: ${TEST_MARKER}"' >> /docker-entrypoint.sh && \
    echo '    pytest -v -m "${TEST_MARKER}" --alluredir=reports/allure-results "$@" || EXIT_CODE=$?' >> /docker-entrypoint.sh && \
    echo '    ;;' >> /docker-entrypoint.sh && \
    echo '  *)' >> /docker-entrypoint.sh && \
    echo '    echo ">>> 未知模式: ${TEST_MODE}，执行默认冒烟测试"' >> /docker-entrypoint.sh && \
    echo '    pytest -v -m smoke --alluredir=reports/allure-results "$@" || EXIT_CODE=$?' >> /docker-entrypoint.sh && \
    echo '    ;;' >> /docker-entrypoint.sh && \
    echo 'esac' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# 生成 Allure 报告' >> /docker-entrypoint.sh && \
    echo 'echo "========================================="' >> /docker-entrypoint.sh && \
    echo 'echo "生成 Allure HTML 报告..."' >> /docker-entrypoint.sh && \
    echo 'echo "========================================="' >> /docker-entrypoint.sh && \
    echo 'allure generate reports/allure-results -o reports/allure-report --clean || true' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo 'echo "========================================="' >> /docker-entrypoint.sh && \
    echo 'echo "报告已生成: /app/reports/allure-report/index.html"' >> /docker-entrypoint.sh && \
    echo 'echo "========================================="' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo 'exit $EXIT_CODE' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import pytest; import allure" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]