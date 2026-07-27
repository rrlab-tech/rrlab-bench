#!/usr/bin/env python3
"""RRLabBench 象限图 — 使用 matplotlib 生成正式图表"""
import json, sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

MODELS = [
    ('deepseek-v4-pro', 'DS Pro', 3, 6),
    ('deepseek-v4-flash', 'DS Flash', 1, 2),
    ('kimi-k3', 'Kimi K3', 20, 100),
    ('glm-5.2', 'GLM 5.2', 7, 22),
    ('MiniMax-M3', 'MiniMax M3', 2.18, 8.7),
    ('x-ai/grok-4.5', 'Grok 4.5', 14.5, 43.5),
    ('anthropic/claude-opus-4.8', 'Opus 4.8', 36.25, 181.25),
]
SCENARIOS = ['refactor-api', 'fix-bug-cascade', 'add-validation']

def med(v):
    s=sorted(v); n=len(s)
    return s[n//2] if n%2==1 else (s[n//2-1]+s[n//2])/2

rows = []
for mid, label, pi, po in MODELS:
    all_t,all_e,all_tok,all_pt,all_ct = [],[],[],[],[]
    for s in SCENARIOS:
        f = DATA_DIR / f"{s}_{mid.replace('/', '_')}.json"
        try:
            d = json.loads(f.read_text())
            results = d if isinstance(d,list) else d.get('results',[])
            valid = [r for r in results if r and r.get('error') is None]
            if valid:
                all_t += [r['turns'] for r in valid]
                all_e += [r['elapsed'] for r in valid]
                all_tok += [r['total_tokens'] for r in valid]
                all_pt += [r.get('prompt_tokens',0) for r in valid]
                all_ct += [r.get('completion_tokens',0) for r in valid]
        except: pass
    if all_t:
        rows.append((label, med(all_t), med(all_e), med(all_tok), med(all_pt), med(all_ct), pi, po))

# Opus 5 M
for suffix, label in [('', 'Opus 5 M'), ('_max', 'Opus 5 MAX')]:
    all_t,all_e,all_tok,all_pt,all_ct = [],[],[],[],[]
    for s in SCENARIOS:
        f = DATA_DIR / f"{s}_anthropic_claude-opus-5{suffix}.json"
        try:
            d = json.loads(f.read_text())
            results = d if isinstance(d,list) else d.get('results',[])
            valid = [r for r in results if r and r.get('error') is None]
            if valid:
                all_t += [r['turns'] for r in valid]
                all_e += [r['elapsed'] for r in valid]
                all_tok += [r['total_tokens'] for r in valid]
                all_pt += [r.get('prompt_tokens',0) for r in valid]
                all_ct += [r.get('completion_tokens',0) for r in valid]
        except: pass
    if all_t:
        rows.append((label, med(all_t), med(all_e), med(all_tok), med(all_pt), med(all_ct), 36.25, 181.25))

# 计算费用
data = []
for label,tm,em,tkm,pm,cm,pi,po in rows:
    cost = pm/1e6*pi + cm/1e6*po
    tpt = tkm/tm
    ept = em/tm
    data.append({'label':label,'turns':tm,'time':em,'tokens':tkm,'cost':cost,'tpt':tpt,'ept':ept})

# ── 象限图 1: 费用 × 速度 ──
print("## 象限图 1: 费用 × 速度")
print()
print("        快 ↑")
print("           │")
# Split: cost < 0.5 = cheap, time < 60s = fast
for d in sorted(data, key=lambda x: x['time']):
    cost_tag = '便宜' if d['cost'] < 0.5 else '贵  '
    time_tag = '快' if d['time'] < 60 else '慢'
    # 象限位置
    x = int(d['cost'] / max(r['cost'] for r in data) * 40)
    y = int((1 - d['time'] / max(r['time'] for r in data)) * 15)
    quad = f"{cost_tag}+{time_tag}"
    bar_time = '░' * int(d['time'] / 10)
    print(f'{quad} │ {d["label"]:12s} ¥{d["cost"]:<6} {d["time"]:4.0f}s')
print()

# ── 象限图 2: 费用 × 回合 × Token (气泡) ──
print("## 象限图 2: 费用 × 回合 (气泡=Token)")
print()
print("        少回合 ↑")
print("               │")
for d in sorted(data, key=lambda x: x['turns']):
    cost_tag = '便宜' if d['cost'] < 0.5 else '贵  '
    turn_tag = '少轮' if d['turns'] < 10 else '多轮'
    quad = f"{cost_tag}+{turn_tag}"
    bubble = '●' * min(20, int(d['tokens'] / 10000))
    print(f'{quad} │ {d["label"]:12s} ¥{d["cost"]:<6} {d["turns"]:2.0f}轮 {d["tokens"]:>7,.0f}tok {bubble}')
print()

# ── 象限图 3: Token效率 × 回合效率 ──
print("## 象限图 3: Token/回合 × 秒/回合")
print()
print("        每回合快 ↑")
print("                 │")
for d in sorted(data, key=lambda x: x['ept']):
    tpt_tag = '省Token' if d['tpt'] < 5000 else '费Token'
    ept_tag = '快轮' if d['ept'] < 6 else '慢轮'
    quad = f"{tpt_tag}+{ept_tag}"
    bar = '█' * int(d['tpt'] / 1000)
    print(f'{quad:16s} │ {d["label"]:12s} {d["tpt"]:>6,.0f} tok/t  {d["ept"]:.1f}s/t')

# ── 象限分类 ──
print()
print("## 模型分类")
print()
fast_cheap = [d for d in data if d['cost'] < 0.5 and d['time'] < 60]
slow_cheap = [d for d in data if d['cost'] < 0.5 and d['time'] >= 60]
fast_expensive = [d for d in data if d['cost'] >= 0.5 and d['time'] < 60]
slow_expensive = [d for d in data if d['cost'] >= 0.5 and d['time'] >= 60]

print("🟢 快+便宜 (实用区):")
for d in fast_cheap:
    print(f"   {d['label']}")
print(f"\n🟡 慢+便宜 (可接受区):")
for d in slow_cheap:
    print(f"   {d['label']}")
print(f"\n🔵 快+贵 (土豪区):")
for d in fast_expensive:
    print(f"   {d['label']}")
print(f"\n🔴 慢+贵 (不推荐区):")
for d in slow_expensive:
    print(f"   {d['label']}")
