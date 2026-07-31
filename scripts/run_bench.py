#!/usr/bin/env python3
"""
RRLabBench 批量运行脚本

快速上手:
  # 确保已设置环境变量: DEEPSEEK_API_KEY, OPENROUTER_API_KEY 等
  python3 scripts/run_bench.py 3    # 每个场景跑 3 次
  python3 scripts/run_bench.py 5 --models deepseek-v4-pro,kimi-k3

数据保存到 data/ 目录，下次运行自动跳过已完成的。
"""

import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT / "src"))
from core.sandbox import Sandbox, SandboxConfig
from core.tools import ToolExecutor
from core.agent_loop import run_agent_loop
from core.test_runner import TestRunner
from evaluators.frr import compute_frr
import importlib

# ── 配置 ──────────────────────────────────────────

SCENARIOS = ["refactor-api", "fix-bug-cascade", "add-validation"]
MOD_LOOKUP = {
    "refactor-api": "scenarios.refactor_api",
    "fix-bug-cascade": "scenarios.fix_bug_cascade",
    "add-validation": "scenarios.add_validation",
}

# 默认定价（RMB/百万 token）
PRICING = {
    "deepseek-v4-pro":         {"input": 3.0, "output": 6.0},
    "deepseek-v4-flash":       {"input": 1.0, "output": 2.0},
    "kimi-k3":                 {"input": 20.0, "output": 100.0},
    "glm-5.2":                 {"input": 7.0, "output": 22.0},
    "MiniMax-M3":              {"input": 2.18, "output": 8.7},
    "x-ai/grok-4.5":           {"input": 14.5, "output": 43.5},
    "anthropic/claude-opus-5": {"input": 36.25, "output": 181.25},
    "anthropic/claude-opus-4.8":{"input": 36.25, "output": 181.25},
}

# 默认模型列表（确保已在环境变量中设好对应的 API Key）
DEFAULT_MODELS = [
    {"name": "deepseek-v4-pro",   "key_env": "DEEPSEEK_API_KEY",     "url": "https://api.deepseek.com/v1"},
    {"name": "deepseek-v4-flash", "key_env": "DEEPSEEK_API_KEY",     "url": "https://api.deepseek.com/v1"},
    {"name": "kimi-k3",           "key_env": "MOONSHOT_API_KEY",     "url": "https://api.moonshot.cn/v1"},
    {"name": "glm-5.2",           "key_env": "ZHIPU_API_KEY",       "url": "https://open.bigmodel.cn/api/paas/v4"},
    {"name": "MiniMax-M3",        "key_env": "OPENROUTER_API_KEY",   "url": "https://openrouter.ai/api/v1"},
    {"name": "x-ai/grok-4.5",     "key_env": "OPENROUTER_API_KEY",   "url": "https://openrouter.ai/api/v1"},
    {"name": "anthropic/claude-opus-5",   "key_env": "OPENROUTER_API_KEY", "url": "https://openrouter.ai/api/v1"},
    {"name": "anthropic/claude-opus-4.8", "key_env": "OPENROUTER_API_KEY", "url": "https://openrouter.ai/api/v1"},
]


def med(vals):
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2


def run_one(scenario: str, model_cfg: dict, run_idx: int) -> dict:
    """单次运行"""
    mod = importlib.import_module(MOD_LOOKUP[scenario])
    create_project, config = mod.create_project, mod.SCENARIO_CONFIG

    tmpl = Path(tempfile.mkdtemp(prefix=f"bt-{run_idx}-"))
    work = Path(tempfile.mkdtemp(prefix=f"bw-{run_idx}-"))
    create_project(tmpl)

    sb = Sandbox(SandboxConfig(
        template_dir=tmpl,
        work_dir=work,
        trap_files=config.get("trap_files", []),
        target_files=config.get("target_files", []),
    ))

    try:
        sb.setup()
        sb.snapshot_before()

        runner = TestRunner(work, config["test_command"])
        baseline = runner.run()

        executor = ToolExecutor(work)

        api_key = os.environ.get(model_cfg["key_env"])
        if not api_key:
            return {"run": run_idx, "error": f"环境变量 {model_cfg['key_env']} 未设置"}

        result = run_agent_loop(
            model=model_cfg["name"],
            api_key=api_key,
            base_url=model_cfg["url"],
            executor=executor,
            task_prompt=config["task_prompt"],
            max_turns=30,
            temperature=0.7,
        )

        sb.snapshot_after()
        after_test = TestRunner(work, config["test_command"]).run()
        frr_data = compute_frr(baseline, after_test, config.get("expected_new_tests"))

        return {
            "run": run_idx,
            "completed": result["completed"],
            "turns": result["turns"],
            "elapsed": round(result["elapsed"], 1),
            "total_tokens": result.get("total_tokens", 0),
            "prompt_tokens": result.get("prompt_tokens", 0),
            "completion_tokens": result.get("completion_tokens", 0),
            "frr": frr_data,
            "error": result.get("error"),
        }
    finally:
        sb.cleanup()
        shutil.rmtree(tmpl, ignore_errors=True)


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    # 解析 --models 参数
    models = DEFAULT_MODELS
    for arg in sys.argv[2:]:
        if arg.startswith("--models="):
            model_names = arg.split("=", 1)[1].split(",")
            models = [m for m in DEFAULT_MODELS if m["name"] in model_names]
        elif arg.startswith("--scenarios="):
            global SCENARIOS
            SCENARIOS = arg.split("=", 1)[1].split(",")

    # 过滤：只保留 API Key 已配好的
    available = []
    for m in models:
        if os.environ.get(m["key_env"]):
            available.append(m)
        else:
            print(f"⚠️  跳过 {m['name']}（环境变量 {m['key_env']} 未设置）")
    models = available

    print(f"🚀 {len(SCENARIOS)} 场景 × {len(models)} 模型 × {runs} 次 = {len(SCENARIOS) * len(models) * runs} 次运行")
    print(f"   开始: {datetime.now().strftime('%H:%M:%S')}\n")

    t0 = time.time()
    total = len(SCENARIOS) * len(models)
    idx = 0

    for model in models:
        for scenario in SCENARIOS:
            idx += 1
            out_file = DATA_DIR / f"{scenario}_{model['name'].replace('/', '_')}.json"

            # 跳过已完成的
            if out_file.exists():
                try:
                    existing = json.loads(out_file.read_text(encoding="utf-8"))
                    if isinstance(existing, list) and len(existing) >= runs:
                        ok = sum(1 for r in existing if isinstance(r, dict) and r.get("error") is None)
                        if ok >= runs:
                            print(f"\n[{idx}/{total}] {scenario} × {model['name']}  ⏭  跳过")
                            continue
                except Exception:
                    pass

            results = []
            print(f"\n[{idx}/{total}] {scenario} × {model['name']}  ", end="", flush=True)

            for i in range(1, runs + 1):
                r = run_one(scenario, model, i)
                results.append(r)
                sys.stdout.write("." if not r.get("error") else "✗")
                sys.stdout.flush()

            out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

            valid = [r for r in results if isinstance(r, dict) and r.get("error") is None]
            if valid:
                t = [r["turns"] for r in valid]
                e = [r["elapsed"] for r in valid]
                tok = [r["total_tokens"] for r in valid]
                pt = [r.get("prompt_tokens", 0) for r in valid]
                ct = [r.get("completion_tokens", 0) for r in valid]
                frrs = [r["frr"]["frr"] for r in valid]
                p = PRICING.get(model["name"], {"input": 3, "output": 6})
                cost = round(med(pt) / 1e6 * p["input"] + med(ct) / 1e6 * p["output"], 4)
                print(f" ✅ FRR={med(frrs):.0f}% turn={med(t):.0f} {med(e):.0f}s {int(med(tok)):,}tok ¥{cost}")
            else:
                print(" ❌")

    elapsed = time.time() - t0
    print(f"\n✅ 完成 — {elapsed / 60:.1f} 分钟")
    print(f"   结果: {DATA_DIR}/")


if __name__ == "__main__":
    main()
