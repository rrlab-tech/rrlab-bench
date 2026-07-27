"""FRR 评分器单元测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from evaluators.frr import compute_frr


def test_frr_zero():
    """无回归"""
    baseline = {
        "success": True,
        "passed": ["t1", "t2", "t3"],
        "failed": [],
        "errors": [],
        "total": 3,
    }
    after = {
        "success": True,
        "passed": ["t1", "t2", "t3"],
        "failed": [],
        "errors": [],
        "total": 3,
    }
    r = compute_frr(baseline, after)
    assert r["frr"] == 0.0
    assert r["regressed_tests"] == []
    assert not r["code_broken"]


def test_frr_full_regression():
    """全部回归"""
    baseline = {
        "success": True,
        "passed": ["t1", "t2"],
        "failed": [],
        "errors": [],
        "total": 2,
    }
    after = {
        "success": False,
        "passed": [],
        "failed": ["t1", "t2"],
        "errors": [],
        "total": 2,
    }
    r = compute_frr(baseline, after)
    assert r["frr"] == 100.0
    assert len(r["regressed_tests"]) == 2


def test_frr_partial():
    """部分回归"""
    baseline = {
        "success": True,
        "passed": ["t1", "t2", "t3", "t4"],
        "failed": [],
        "errors": [],
        "total": 4,
    }
    after = {
        "success": False,
        "passed": ["t1", "t2"],
        "failed": ["t3", "t4"],
        "errors": [],
        "total": 4,
    }
    r = compute_frr(baseline, after)
    assert r["frr"] == 50.0


def test_frr_code_broken():
    """代码彻底跑不起来"""
    baseline = {
        "success": True,
        "passed": ["t1", "t2", "t3"],
        "failed": [],
        "errors": [],
        "total": 3,
    }
    after = {
        "success": False,
        "passed": [],
        "failed": [],
        "errors": ["ModuleNotFoundError"],
        "total": 0,
    }
    r = compute_frr(baseline, after)
    assert r["frr"] == 100.0
    assert r["code_broken"]


def test_frr_tcr():
    """TCR 计算"""
    baseline = {
        "success": True,
        "passed": ["old1"],
        "failed": [],
        "errors": [],
        "total": 1,
    }
    after = {
        "success": True,
        "passed": ["old1", "new1", "new2"],
        "failed": [],
        "errors": [],
        "total": 3,
    }
    r = compute_frr(baseline, after, expected_new_tests=["new1", "new2"])
    assert r["tcr"] == 100.0
    assert r["frr"] == 0.0


def test_frr_fixed():
    """修复了此前失败的测试"""
    baseline = {
        "success": False,
        "passed": ["t1"],
        "failed": ["t2"],
        "errors": [],
        "total": 2,
    }
    after = {
        "success": True,
        "passed": ["t1", "t2"],
        "failed": [],
        "errors": [],
        "total": 2,
    }
    r = compute_frr(baseline, after)
    assert r["frr"] == 0.0
    assert r["fixed_tests"] == ["t2"]
