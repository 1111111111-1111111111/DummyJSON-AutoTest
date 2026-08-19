#!/bin/bash
# ============================================================
# Docker 容器入口脚本
# 根据环境变量 TEST_MODE 执行对应测试模式，
# 测试完成后生成 Allure 报告，并按退出码反映成功/失败。
# ============================================================
set -e

MODE="${TEST_MODE:-all}"

echo "============================================================"
echo "  DummyJSON API 自动化测试 — 容器内执行"
echo "  测试模式: ${MODE}"
echo "  执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# 执行测试入口脚本
python run_tests.py --mode "${MODE}"
TEST_EXIT_CODE=$?

echo "------------------------------------------------------------"
echo "  测试执行结束，退出码: ${TEST_EXIT_CODE}"
if [ ${TEST_EXIT_CODE} -eq 0 ]; then
    echo "  状态: ✅ ALL PASSED"
else
    echo "  状态: ❌ SOME TESTS FAILED"
fi
echo "------------------------------------------------------------"

# Allure 报告已由 run_tests.py 生成，无需重复
exit ${TEST_EXIT_CODE}
