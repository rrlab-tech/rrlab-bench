#!/usr/bin/env python3
"""
harness_log — Bench-Harness 每日实验数据记录

每天手动闭环后运行一次，把 pi-reflect 运行结果 + 探针结果追加到
data/harness-log/harness-log.jsonl（JSONL，一天一行）。

用法:
  python3 scripts/harness_log.py --date 2026-07-31 \
      --probe-file /tmp/probe_0731.json \
      --bad-edits 2 --total-edits 6 \
      --note "merge吞句+重复行,已手动修复"

参数:
  --date          日期（默认今天）
  --probe-file    探针结果 JSON（rrlab-bench probe -o 输出），可选
  --total-edits   pi-reflect 应用编辑数（从 reflect-history.json 自动读，可覆盖）
  --bad-edits     diff 检查发现的有害编辑数
  --note          备注
"""

import argparse
import json
from datetime import date as dt_date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG_DIR = REPO / "data" / "harness-log"
LOG_FILE = LOG_DIR / "harness-log.jsonl"
REFLECT_HISTORY = Path.home() / ".pi" / "agent" / "reflect-history.json"


def load_reflect_entry(date_str: str) -> dict | None:
    """从 reflect-history.json 找该日期对应的记录（按 UTC 日期匹配）"""
    if not REFLECT_HISTORY.exists():
        return None
    history = json.load(open(REFLECT_HISTORY))
    for entry in reversed(history):
        ts = entry.get("timestamp", "")
        # timestamp 是 UTC，本地 +8 的凌晨 4 点 = UTC 前一天 20 点
        # 匹配：UTC 日期 == date_str 或 date_str 前一天
        if ts[:10] in (date_str, _prev_day(date_str)):
            return entry
    return None


def _prev_day(date_str: str) -> str:
    y, m, d = map(int, date_str.split("-"))
    from datetime import timedelta
    return (dt_date(y, m, d) - timedelta(days=1)).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt_date.today().isoformat())
    ap.add_argument("--probe-file", help="probe -o 输出的 JSON 文件")
    ap.add_argument("--total-edits", type=int, help="覆盖自动读取的编辑数")
    ap.add_argument("--bad-edits", type=int, default=0)
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    # pi-reflect 信息
    reflect_entry = load_reflect_entry(args.date)
    record = {
        "date": args.date,
        "reflect": {
            "ran": reflect_entry is not None,
            "sessions_analyzed": reflect_entry.get("sessionsAnalyzed") if reflect_entry else 0,
            "edits_applied": args.total_edits if args.total_edits is not None
                            else (reflect_entry.get("editsApplied") if reflect_entry else 0),
            "bad_edits": args.bad_edits,
            "summary": reflect_entry.get("summary", "") if reflect_entry else "",
        },
        "probes": None,
        "note": args.note,
    }

    # 探针信息
    if args.probe_file and Path(args.probe_file).exists():
        probe_data = json.load(open(args.probe_file))
        record["probes"] = {
            "total": len(probe_data),
            "passed": sum(1 for p in probe_data if p.get("passed")),
            "results": [
                {"name": p["probe"], "passed": p["passed"],
                 "tools": p.get("tool_sequence", [])}
                for p in probe_data
            ],
        }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    r = record["reflect"]
    p = record["probes"]
    print(f"✅ logged {args.date}")
    print(f"   reflect: ran={r['ran']} edits={r['edits_applied']} bad={r['bad_edits']}")
    if p:
        print(f"   probes:  {p['passed']}/{p['total']} passed")
    print(f"   → {LOG_FILE}")


if __name__ == "__main__":
    main()
