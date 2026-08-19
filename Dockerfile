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

# --------- 直接使用 CMD，不依赖外部脚本 ---------
# 默认执行所有测试
CMD ["sh", "-c", "pytest -v --alluredir=reports/allure-results && allure generate reports/allure-results -o reports/allure-report --clean || true"]