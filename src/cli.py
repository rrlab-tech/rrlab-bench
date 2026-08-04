"""
CLI — RRLabBench v0.3

FRR (Functional Regression Risk) — test regression risk assessment after Agent code modifications.

Usage:
  python3 -m src.cli audit --scenario refactor-api --model deepseek-v4-pro --runs 5
  rrlab-bench run --model deepseek-v4-pro --all-scenarios --runs 3
  rrlab-bench submit --file results.json
"""

import argparse
import importlib
import json
import os
import shutil
import sys
import tempfile
import time
import webbrowser
import urllib.parse
from pathlib import Path
from datetime import datetime
from statistics import median

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from core.sandbox import Sandbox, SandboxConfig
    from core.tools import ToolExecutor
    from core.agent_loop import run_agent_loop
    from core.test_runner import TestRunner
    from evaluators.frr import compute_frr
    from evaluators.test_integrity import check_test_integrity
else:
    from .core.sandbox import Sandbox, SandboxConfig
    from .core.tools import ToolExecutor
    from .core.agent_loop import run_agent_loop
    from .core.test_runner import TestRunner
    from .evaluators.frr import compute_frr
    from .evaluators.test_integrity import check_test_integrity


SCENARIOS = {
    "refactor-api": "scenarios.refactor_api",
    "fix-bug-cascade": "scenarios.fix_bug_cascade",
    "add-validation": "scenarios.add_validation",
}

# Default pricing (RMB / 1M tokens)
PRICING = {
    "deepseek-v4-pro":   {"input": 3.0, "output": 6.0},
    "deepseek-v4-flash": {"input": 1.0, "output": 2.0},
    "glm-5.2":           {"input": 7.0, "output": 22.0},
    "kimi-k3":           {"input": 20.0, "output": 100.0},
    "MiniMax-M3":        {"input": 2.18, "output": 8.7},
    "x-ai/grok-4.5":     {"input": 14.5, "output": 43.5},
    "anthropic/claude-opus-5":   {"input": 36.25, "output": 181.25},
    "anthropic/claude-opus-5_max": {"input": 36.25, "output": 181.25},
    "openai/gpt-5.6-luna":         {"input": 0.73, "output": 4.38},  # $0.10/$0.60 50% off
}


def _load_scenario(name: str):
    mod_name = SCENARIOS.get(name)
    if mod_name is None:
        print(f"Error: unknown scenario '{name}'. Available: {', '.join(SCENARIOS)}")
        sys.exit(1)
    # 兼容两种运行方式：
    #   模块模式（python3 -m src.cli）→ 包前缀 src.，导入 src.scenarios.X
    #   脚本模式（cd src && python3 cli.py）→ __package__ 为 None，导入 scenarios.X
    if __package__:
        mod_name = f"{__package__}.{mod_name}"
    mod = importlib.import_module(mod_name)
    return mod.create_project, mod.SCENARIO_CONFIG


def _resolve_model_config(model: str, api_key: str = None, base_url: str = None):
    """Auto-infer API configuration"""
    if base_url:
        url = base_url
    elif "glm" in model.lower() or "zhipu" in model.lower():
        url = "https://open.bigmodel.cn/api/paas/v4"
    elif "kimi" in model.lower():
        url = "https://api.kimi.com/coding"
    elif "/" in model:
        url = "https://openrouter.ai/api/v1"
    else:
        url = "https://api.deepseek.com/v1"

    if api_key:
        key = api_key
    elif "glm" in model.lower() or "zhipu" in model.lower():
        key = os.environ.get("ZHIPU_API_KEY")
    elif "kimi" in model.lower():
        key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
    elif "/" in model:
        key = os.environ.get("OPENROUTER_API_KEY")
    else:
        key = os.environ.get("DEEPSEEK_API_KEY")

    # Fallback: 从 Pi auth.json 读取
    if not key:
        auth_path = Path.home() / ".pi" / "agent" / "auth.json"
        if auth_path.exists():
            try:
                auth = json.loads(auth_path.read_text())
                provider_map = {"kimi": "kimi-coding", "deepseek": "deepseek",
                                "glm": "zai", "zhipu": "zai",
                                "openrouter": "openrouter", "minimax": "minimax-cn"}
                pname = None
                if "kimi" in model.lower():
                    pname = "kimi-coding"
                elif "glm" in model.lower() or "zhipu" in model.lower():
                    pname = "zai"
                elif "/" in model:
                    pname = "openrouter"
                else:
                    pname = "deepseek"
                if pname and pname in auth:
                    key = auth[pname].get("key") or auth[pname].get("api_key")
            except Exception:
                pass

    if not key:
        print("Error: No API key found. Set one of these environment variables:")
        print("  DeepSeek:   DEEPSEEK_API_KEY")
        print("  Kimi:       KIMI_API_KEY or MOONSHOT_API_KEY")
        print("  GLM:        ZHIPU_API_KEY")
        print("  OpenRouter: OPENROUTER_API_KEY")
        print("Or ensure ~/.pi/agent/auth.json exists with the corresponding provider key.")
        sys.exit(1)

    return key, url


def _run_single_audit(model: str, api_key: str, base_url: str, scenario_name: str, run_idx: int,
                      harness_text: str | None = None) -> dict:
    """Run a single audit"""
    create_project, config = _load_scenario(scenario_name)
    template_dir = Path(tempfile.mkdtemp(prefix=f"rrlab-template-{run_idx}-"))
    work_dir = Path(tempfile.mkdtemp(prefix=f"rrlab-sandbox-{run_idx}-"))

    create_project(template_dir)

    sandbox = Sandbox(SandboxConfig(
        template_dir=template_dir,
        work_dir=work_dir,
        trap_files=config.get("trap_files", []),
        target_files=config.get("target_files", []),
    ))

    try:
        sandbox.setup()
        sandbox.snapshot_before()

        runner = TestRunner(work_dir, config["test_command"])
        baseline_test = runner.run()

        executor = ToolExecutor(work_dir)
        result = run_agent_loop(
            model=model,
            api_key=api_key,
            base_url=base_url,
            executor=executor,
            task_prompt=config["task_prompt"],
            max_turns=30,
            temperature=0.7,
            harness_text=harness_text,
        )

        sandbox.snapshot_after()

        runner2 = TestRunner(work_dir, config["test_command"])
        after_test = runner2.run()
        frr_data = compute_frr(
            baseline_test,
            after_test,
            config.get("expected_new_tests"),
        )

        integrity_data = check_test_integrity(
            sandbox._before_files,
            sandbox._after_files,
        )

        price = PRICING.get(model, {"input": 3.0, "output": 6.0})
        ptok = result.get("prompt_tokens", 0)
        ctok = result.get("completion_tokens", 0)
        cost = round(ptok / 1e6 * price["input"] + ctok / 1e6 * price["output"], 4)

        return {
            "run": run_idx,
            "scenario": config["name"],
            "model": model,
            "completed": result["completed"],
            "turns": result["turns"],
            "elapsed": round(result["elapsed"], 1),
            "error": result.get("error"),
            "frr": frr_data,
            "integrity": integrity_data,
            "tool_calls_count": len(executor.call_log),
            "total_tokens": result.get("total_tokens", 0),
            "prompt_tokens": ptok,
            "completion_tokens": ctok,
            "cost_rmb": cost,
        }

    finally:
        sandbox.cleanup()
        shutil.rmtree(template_dir, ignore_errors=True)


def _print_summary(results: list[dict]):
    n = len(results)
    frr_vals = sorted([r["frr"]["frr"] for r in results if r.get("frr")])
    tcr_vals = sorted([r["frr"]["tcr"] for r in results if r.get("frr") and r["frr"].get("tcr") is not None])
    broken = sum(1 for r in results if r.get("frr") and r["frr"].get("code_broken"))
    cheating = sum(1 for r in results if r.get("integrity") and r["integrity"].get("severity") == "cheating")
    turns = [r["turns"] for r in results]
    elapsed = [r["elapsed"] for r in results]
    tokens = [r.get("total_tokens", 0) for r in results]
    costs = [r.get("cost_rmb", 0) for r in results]

    print(f"\nSummary ({n}/{n} runs)")
    print(f"   FRR median:    {median(frr_vals):.1f}%" if frr_vals else "   FRR: N/A")
    print(f"   FRR worst:     {max(frr_vals):.1f}%" if frr_vals else "")
    print(f"   TCR median:    {median(tcr_vals):.1f}%" if tcr_vals else "")
    print(f"   Code broken:   {broken}/{n}")
    print(f"   Test tampering:{cheating}/{n}")
    print(f"   Avg turns:     {sum(turns) / n:.1f}")
    print(f"   Avg time:      {sum(elapsed) / n:.1f}s")
    print(f"   Avg tokens:    {sum(tokens) / n:,.0f}")
    print(f"   Avg cost:      ¥{sum(costs) / n:.4f}")


def _save_report(results: list[dict], config: dict, model: str, runs: int, path: str):
    output = {
        "scenario": config["name"],
        "model": model,
        "runs": runs,
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }
    Path(path).write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Report saved: {path}")


def cmd_submit(args):
    """Submit audit results to the RRLabBench community (opens GitHub Issue)"""

    # Find the latest results file
    result_files = sorted(
        [f for f in Path(args.data_dir).glob("*.json") if f.name != "summary.json"],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if args.file:
        filepath = Path(args.file)
    elif result_files:
        filepath = result_files[0]
    else:
        print("Error: No results file found.")
        print("Tip: Run audit with -o results.json first, then: rrlab-bench submit --file results.json")
        sys.exit(1)

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error: Failed to parse JSON: {e}")
        sys.exit(1)

    # Extract model and scenario info
    results = data if isinstance(data, list) else data.get("results", [])
    if not results:
        print("Error: No data in results file")
        sys.exit(1)

    # Model: data > CLI arg > filename > unknown
    model_name = args.model or results[0].get("model", "")
    if not model_name:
        stem = filepath.stem
        parts = stem.split("_", 1)
        model_name = parts[1] if len(parts) > 1 else "Unknown model"

    # Scenario: data > CLI arg > filename
    scenarios = args.scenarios or list(set(
        r.get("scenario", "") for r in results if r.get("scenario")
    ))
    if not scenarios:
        stem = filepath.stem
        parts = stem.split("_", 1)
        scenarios = [parts[0]] if len(parts) > 0 else ["?"]

    # Compute summary
    valid = [r for r in results if isinstance(r, dict) and r.get("error") is None]
    if valid:
        turns = sorted([r["turns"] for r in valid])
        elapsed = sorted([r["elapsed"] for r in valid])
        tokens = sorted([r.get("total_tokens", 0) for r in valid])
        costs = sorted([r.get("cost_rmb", 0) for r in valid])
        frrs = sorted([r["frr"]["frr"] for r in valid if r.get("frr")])
        mid = len(turns) // 2
        summary_lines = [
            f"- Turns: {turns[mid]:.0f} (median)",
            f"- Time: {elapsed[mid]:.1f}s",
            f"- Tokens: {tokens[mid]:,}",
            f"- Cost: ¥{costs[mid]:.4f}",
            f"- FRR: {frrs[mid]:.1f}%" if frrs else "- FRR: N/A",
        ]
    else:
        summary_lines = ["- All runs failed"]

    title = f"[Data] {model_name} — {', '.join(scenarios[:3])}"
    body = f"""## Audit Results

**Model**: {model_name}
**Scenarios**: {", ".join(scenarios)}
**Runs**: {len(results)}
**Thinking level**: max

### Summary

{chr(10).join(summary_lines)}

### Raw data

```json
{json.dumps(results, indent=2, ensure_ascii=False)}
```
"""

    url = (
        f"https://github.com/rrlab-tech/rrlab-bench/issues/new"
        f"?title={urllib.parse.quote(title)}"
        f"&body={urllib.parse.quote(body)}"
        f"&labels=community-data"
    )

    print(f"\nSubmitting: {model_name}")
    print(f"   Scenarios: {', '.join(scenarios)}")
    print(f"   Records: {len(results)}")
    print(f"\nOpening GitHub Issue...")
    print(f"   If the browser doesn't open, visit:")
    print(f"   {url[:100]}...")

    webbrowser.open(url)


def cmd_run(args):
    """Run audit: all scenarios × one model"""
    scenarios = list(SCENARIOS.keys()) if args.all_scenarios else [args.scenario]
    all_results = []

    harness_text = None
    if getattr(args, "harness", None):
        harness_text = Path(args.harness).read_text(encoding="utf-8")
        print(f"Harness: {args.harness} ({len(harness_text)} chars)")

    for name in scenarios:
        _, config = _load_scenario(name)
        api_key, base_url = _resolve_model_config(args.model, args.api_key, args.base_url)

        print(f"\n{'='*60}")
        print(f"RRLabBench v0.3 | {config['name']} | {args.model} ×{args.runs}")
        print(f"Task: {config['description']}")
        print(f"{'='*60}")

        results = []
        for i in range(1, args.runs + 1):
            sys.stdout.write(f"  [{i}/{args.runs}] ")
            sys.stdout.flush()
            run_data = _run_single_audit(args.model, api_key, base_url, name, i,
                                         harness_text=harness_text)

            if run_data.get("error"):
                print(f"FAIL {run_data['error'][:60]}")
                continue

            results.append(run_data)
            frr = run_data.get("frr", {})
            pct = frr.get("frr", "?") if frr else "?"
            print(f"ok FRR={pct}% turns={run_data['turns']} {run_data['elapsed']}s ¥{run_data.get('cost_rmb', 0)}")

        if results:
            _print_summary(results)
            all_results.extend(results)

    if args.output and all_results:
        _save_report(all_results, config, args.model, args.runs, args.output)


def cmd_probe(args):
    """Run harness rule probes: baseline vs harness-injected comparison"""
    if __package__ is None:
        from probes.runner import run_probe
    else:
        from .probes.runner import run_probe

    if args.probe:
        probe_files = [Path(args.probe)]
    else:
        probe_files = sorted(Path(args.probes_dir).glob("*.json"))
    if not probe_files:
        print(f"No probes found in {args.probes_dir}/")
        return

    api_key, base_url = _resolve_model_config(args.model, args.api_key, args.base_url)

    harness_text = None
    if args.harness:
        harness_text = Path(args.harness).read_text(encoding="utf-8")

    mode = f"WITH harness ({args.harness})" if harness_text else "BASELINE (no harness)"
    print(f"\n{'='*60}")
    print(f"RRLabBench Probe | {args.model} | {mode}")
    print(f"{'='*60}")

    results = []
    for pf in probe_files:
        r = run_probe(pf, model=args.model, api_key=api_key, base_url=base_url,
                      harness_text=harness_text)
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"\n  [{status}] {r['probe']} — {r['rule']}")
        for c in r["checks"]:
            mark = "✓" if c["passed"] else "✗"
            print(f"      {mark} {c['assertion']['type']}: {c['detail']}")
        print(f"      tools: {' → '.join(r['tool_sequence'])}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n{'='*60}")
    print(f"Probes: {passed}/{len(results)} passed")

    if args.output:
        Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"Saved: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        prog="rrlab-bench",
        description="RRLabBench — Agent capability audit framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  rrlab-bench audit --model deepseek-v4-pro --all-scenarios --runs 3
  rrlab-bench submit --file results.json
  rrlab-bench run --model kimi-k3 --scenario refactor-api --runs 5

Environment variables:
  DEEPSEEK_API_KEY    DeepSeek API key
  KIMI_API_KEY    Kimi API key (or MOONSHOT_API_KEY)
  OPENROUTER_API_KEY  OpenRouter API key (for Claude, GLM, etc.)
""",
    )
    subparsers = parser.add_subparsers(dest="command")

    # audit
    ap = subparsers.add_parser("audit", help="Run agent audit")
    ap.add_argument("--scenario", default="refactor-api",
                    help=f"Scenario: {', '.join(SCENARIOS)}")
    ap.add_argument("--all-scenarios", action="store_true", help="Run all scenarios")
    ap.add_argument("--model", default="deepseek-v4-pro", help="Model ID")
    ap.add_argument("--api-key", help="API key (optional, reads from env)")
    ap.add_argument("--base-url", help="API base URL (auto-detected)")
    ap.add_argument("--runs", type=int, default=5, help="Repeat count (default: 5)")
    ap.add_argument("--harness", help="Harness rules file (e.g. AGENTS.md) to inject into system prompt")
    ap.add_argument("--output", "-o", help="Save JSON report to path")

    # submit
    sp = subparsers.add_parser("submit", help="Submit results to community")
    sp.add_argument("--file", "-f", help="Results JSON file (auto-detect latest if omitted)")
    sp.add_argument("--data-dir", default="data", help="Directory to scan (default: data/)")
    sp.add_argument("--model", "-m", help="Model name (reads from data if omitted)")
    sp.add_argument("--scenarios", "-s", nargs="+", help="Scenario names (reads from data if omitted)")

    # run (short alias)
    rp = subparsers.add_parser("run", help="Short alias for audit")
    rp.add_argument("--scenario", default="refactor-api",
                    help=f"Scenario: {', '.join(SCENARIOS)}")
    rp.add_argument("--all-scenarios", action="store_true", help="Run all scenarios")
    rp.add_argument("--model", default="deepseek-v4-pro", help="Model ID")
    rp.add_argument("--api-key", help="API key")
    rp.add_argument("--base-url", help="API base URL")
    rp.add_argument("--runs", type=int, default=3, help="Repeat count (default: 3)")
    rp.add_argument("--harness", help="Harness rules file to inject into system prompt")
    rp.add_argument("--output", "-o", help="Save JSON report to path")

    # probe
    pp = subparsers.add_parser("probe", help="Run harness rule probes (Bench-Harness v0.1)")
    pp.add_argument("--probe", help="Single probe JSON file (default: all in probes/)")
    pp.add_argument("--probes-dir", default="probes", help="Probes directory (default: probes/)")
    pp.add_argument("--model", default="deepseek-v4-flash", help="Model ID")
    pp.add_argument("--api-key", help="API key")
    pp.add_argument("--base-url", help="API base URL")
    pp.add_argument("--harness", help="Harness rules file (e.g. AGENTS.md) — omit for baseline")
    pp.add_argument("--output", "-o", help="Save JSON report to path")

    args = parser.parse_args()

    if args.command in ("audit", "run"):
        cmd_run(args)
    elif args.command == "submit":
        cmd_submit(args)
    elif args.command == "probe":
        cmd_probe(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
