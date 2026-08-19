#!/bin/bash
set -e

# 默认值
TEST_MODE=${TEST_MODE:-"smoke"}
TEST_MARKER=${TEST_MARKER:-""}
EXIT_CODE=0

echo "========================================="
echo "DummyJSON API 测试容器"
echo "测试模式: ${TEST_MODE}"
[ -n "$TEST_MARKER" ] && echo "测试标记: ${TEST_MARKER}"
echo "========================================="

case ${TEST_MODE} in
  "smoke")
    echo ">>> 执行冒烟测试"
    pytest -v -m smoke --alluredir=reports/allure-results "$@" || EXIT_CODE=$?
    ;;
  "regression")
    echo ">>> 执行回归测试"
    pytest -v -m regression --alluredir=reports/allure-results "$@" || EXIT_CODE=$?
    ;;
  "all")
    echo ">>> 执行全部测试"
    pytest -v --alluredir=reports/allure-results "$@" || EXIT_CODE=$?
    ;;
  "custom")
    echo ">>> 执行自定义测试: ${TEST_MARKER}"
    pytest -v -m "${TEST_MARKER}" --alluredir=reports/allure-results "$@" || EXIT_CODE=$?
    ;;
  *)
    echo ">>> 未知模式: ${TEST_MODE}，执行默认冒烟测试"
    pytest -v -m smoke --alluredir=reports/allure-results "$@" || EXIT_CODE=$?
    ;;
esac

# 无论测试结果如何，生成 Allure 报告
echo "========================================="
echo "生成 Allure HTML 报告..."
echo "========================================="
allure generate reports/allure-results -o reports/allure-report --clean

echo "========================================="
echo "报告已生成: /app/reports/allure-report/index.html"
echo "========================================="

exit $EXIT_CODE