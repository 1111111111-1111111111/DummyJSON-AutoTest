"""
测试执行入口脚本

支持三种执行模式：
    python run_tests.py --mode smoke       # 仅执行冒烟测试
    python run_tests.py --mode regression  # 仅执行全量回归测试
    python run_tests.py --mode all         # 先冒烟，全部通过后再回归

执行流程:
    1. smoke 模式: 仅运行 @pytest.mark.smoke 标记的用例
    2. regression 模式: 仅运行 @pytest.mark.regression 标记的用例
    3. all 模式: 先执行冒烟测试，如果全部通过则自动执行全量回归测试；
       如果冒烟测试失败则立即停止，不执行回归测试
"""
import argparse
import subprocess
import sys
import os
import time
from pathlib import Path

from src.core.logger import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# Allure 结果目录
ALLURE_RESULTS_DIR = PROJECT_ROOT / "reports" / "allure-results"
ALLURE_REPORT_DIR = PROJECT_ROOT / "reports" / "allure-report"

def run_smoke_tests() -> bool:
    """
    执行冒烟测试。

    Returns:
        bool: 全部通过返回 True，否则返回 False
    """
    logger.info("=" * 60)
    logger.info("开始执行冒烟测试 (Smoke Tests)")
    logger.info("=" * 60)

    cmd = [
        sys.executable, "-m", "pytest",
        "-m", "smoke",
        f"--alluredir={ALLURE_RESULTS_DIR}",
        "--clean-alluredir",
        "-v",
        "--tb=short",
        f"{PROJECT_ROOT / 'tests'}",
    ]

    start_time = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.time() - start_time

    if result.returncode == 0:
        logger.info(f"冒烟测试全部通过! 耗时: {elapsed:.1f}s")
        return True
    else:
        logger.error(f"冒烟测试失败! 退出码={result.returncode} 耗时: {elapsed:.1f}s")
        logger.error("冒烟测试未通过，跳过全量回归测试。")
        return False


def run_regression_tests() -> bool:
    """
    执行全量回归测试。

    Returns:
        bool: 全部通过返回 True，否则返回 False
    """
    logger.info("=" * 60)
    logger.info("开始执行全量回归测试 (Regression Tests)")
    logger.info("=" * 60)

    cmd = [
        sys.executable, "-m", "pytest",
        "-m", "regression",
        f"--alluredir={ALLURE_RESULTS_DIR}",
        "-v",
        "--tb=long",
        f"{PROJECT_ROOT / 'tests'}",
    ]

    start_time = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.time() - start_time

    if result.returncode == 0:
        logger.info(f"全量回归测试全部通过! 耗时: {elapsed:.1f}s")
        return True
    else:
        logger.error(f"全量回归测试有失败! 退出码={result.returncode} 耗时: {elapsed:.1f}s")
        return False


def run_all_tests() -> bool:
    """
    按顺序执行: 先冒烟，通过后再回归。

    Returns:
        bool: 全部通过返回 True，否则返回 False
    """
    logger.info("=" * 60)
    logger.info("执行模式: ALL (冒烟 + 全量回归)")
    logger.info("=" * 60)

    # Step 1: 冒烟测试
    smoke_passed = run_smoke_tests()

    if not smoke_passed:
        logger.error(">> 冒烟测试未通过，停止执行全量回归测试")
        return False

    logger.info(">> 冒烟测试通过，继续执行全量回归测试...")

    # Step 2: 全量回归测试
    regression_passed = run_regression_tests()

    if smoke_passed and regression_passed:
        logger.info("=" * 60)
        logger.info("ALL 所有测试通过!")
        logger.info("=" * 60)
        return True
    else:
        logger.error("ALL 部分测试未通过")
        return False


def main():
    """主函数，解析命令行参数并执行对应模式的测试。"""
    parser = argparse.ArgumentParser(
        description="DummyJSON API 自动化测试执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行示例:
  python run_tests.py --mode smoke       # 仅执行冒烟测试
  python run_tests.py --mode regression  # 仅执行全量回归测试
  python run_tests.py --mode all         # 先冒烟，通过后再回归
  allure serve reports/allure-results    # 查看 Allure 报告
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["smoke", "regression", "all"],
        default="all",
        help="测试执行模式: smoke=冒烟测试, regression=全量回归, all=先冒烟再回归 (默认: all)",
    )
    args = parser.parse_args()

    logger.info(f"测试执行模式: {args.mode}")

    # 确保结果目录存在
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ALLURE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # 根据模式执行
    if args.mode == "smoke":
        success = run_smoke_tests()
    elif args.mode == "regression":
        success = run_regression_tests()
    else:
        success = run_all_tests()

    # 输出最终结果
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("测试执行完成: ALL PASSED")
        # logger.info(f"Allure 报告: allure serve {ALLURE_RESULTS_DIR}")
        logger.info(f"Allure 报告: ")
        cmd = f"allure generate {ALLURE_RESULTS_DIR} -o {ALLURE_REPORT_DIR} --clean"
        result = subprocess.run(cmd, shell=True)
        logger.info(result.stdout)
        logger.info(result.stderr)
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 60)
        logger.error("测试执行完成: SOME TESTS FAILED")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
