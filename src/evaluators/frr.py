"""
FRR 评分器 — 功能回归率计算

对比 Agent 执行前后的测试结果，计算功能回归率、任务完成率。
"""


def compute_frr(
    baseline: dict,
    after: dict,
    expected_new_tests: list[str] | None = None,
) -> dict:
    """
    计算功能回归率

    Args:
        baseline: 执行前 TestRunner.run() 的结果
        after:    执行后 TestRunner.run() 的结果
        expected_new_tests: 任务应新增/通过的测试（用于计算 TCR）

    Returns:
        {
          "frr": float,
          "regressed_tests": list[str],
          "fixed_tests": list[str],
          "tcr": float | None,
          "new_tests_passed": list[str],
          "new_tests_failed": list[str],
          "code_broken": bool,
          "baseline_pass_count": int,
          "after_pass_count": int,
        }
    """

    # 情况 1：代码根本跑不起来（import/syntax 错误，不是测试失败）
    after_errors = after.get("errors", [])
    code_broken = (
        not after.get("success")
        and baseline.get("success")
        and after_errors
        and any("ModuleNotFoundError" in e or "ImportError" in e or "SyntaxError" in e for e in after_errors)
    )
    if code_broken:
        return {
            "frr": 100.0,
            "regressed_tests": [],
            "fixed_tests": [],
            "tcr": 0.0 if expected_new_tests else None,
            "new_tests_passed": [],
            "new_tests_failed": expected_new_tests or [],
            "code_broken": True,
            "baseline_pass_count": len(baseline.get("passed", [])),
            "after_pass_count": 0,
        }

    baseline_passed = set(baseline.get("passed", []))
    baseline_failed = set(baseline.get("failed", []))
    after_passed = set(after.get("passed", []))
    after_failed = set(after.get("failed", []))

    # 从 PASS 变 FAIL/ERROR 的测试
    regressed = baseline_passed & (after_failed | set(after.get("errors", [])))

    # 从 FAIL 变 PASS 的测试（可能是好事）
    fixed = baseline_failed & after_passed

    # FRR
    baseline_pass_count = len(baseline_passed)
    frr = (len(regressed) / baseline_pass_count * 100.0) if baseline_pass_count > 0 else 0.0

    # TCR
    tcr = None
    new_passed = []
    new_failed = []
    if expected_new_tests:
        new_passed = [t for t in expected_new_tests if t in after_passed]
        new_failed = [t for t in expected_new_tests if t not in after_passed]
        tcr = (len(new_passed) / len(expected_new_tests) * 100.0) if expected_new_tests else 100.0

    return {
        "frr": round(frr, 1),
        "regressed_tests": sorted(regressed),
        "fixed_tests": sorted(fixed),
        "tcr": round(tcr, 1) if tcr is not None else None,
        "new_tests_passed": sorted(new_passed),
        "new_tests_failed": sorted(new_failed),
        "code_broken": False,
        "baseline_pass_count": baseline_pass_count,
        "after_pass_count": len(after_passed),
    }
