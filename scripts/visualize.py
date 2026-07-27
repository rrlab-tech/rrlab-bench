#!/usr/bin/env python3
"""RRLabBench 可视化 — 从 data/ 读取最终排名数据生成图表"""
import json, sys, subprocess, tempfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

MODELS = [
    ('deepseek-v4-pro', 'DS Pro', 3, 6, '1M'),
    ('deepseek-v4-flash', 'DS Flash', 1, 2, '1M'),
    ('kimi-k3', 'Kimi K3', 20, 100, '1M'),
    ('glm-5.2', 'GLM 5.2', 7, 22, '1M'),
    ('MiniMax-M3', 'MiniMax M3', 2.18, 8.7, '1M'),
    ('x-ai/grok-4.5', 'Grok 4.5', 14.5, 43.5, '500K'),
    ('anthropic/claude-opus-4.8', 'Opus 4.8', 36.25, 181.25, '1M'),
]
SCENARIOS = ['refactor-api', 'fix-bug-cascade', 'add-validation']

def med(v):
    s=sorted(v); n=len(s)
    return s[n//2] if n%2==1 else (s[n//2-1]+s[n//2])/2

# 收集数据
rows = []
for mid, label, pi, po, ctx in MODELS:
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
        tm,em,tkm = med(all_t), med(all_e), med(all_tok)
        pm,cm = med(all_pt), med(all_ct)
        cost = round(pm/1e6*pi + cm/1e6*po, 4)
        rows.append((label, tm, em, tkm, cost, ctx))

# Opus 5 special
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
        tm,em,tkm = med(all_t), med(all_e), med(all_tok)
        pm,cm = med(all_pt), med(all_ct)
        cost = round(pm/1e6*36.25 + cm/1e6*181.25, 4)
        rows.append((label, tm, em, tkm, cost, '1M'))

# ── ASCII 图表 ──

# 1. 综合排名条
print("═══ 综合排名 ═══\n")
best_cost, best_time, best_turns, best_tokens = rows[0][4], rows[0][2], rows[0][1], rows[0][3]
for r in rows:
    if r[4] < best_cost: best_cost = r[4]
    if r[2] < best_time: best_time = r[2]
    if r[1] < best_turns: best_turns = r[1]
    if r[3] < best_tokens: best_tokens = r[3]

scored = []
for r in rows:
    label,tm,em,tkm,cost,ctx = r
    s_c = best_cost/cost*0.30
    s_t = best_time/em*0.30
    s_u = best_turns/tm*0.20
    s_k = best_tokens/tkm*0.20
    total = s_c+s_t+s_u+s_k
    scored.append((label,tm,em,tkm,cost,total))

scored.sort(key=lambda x: x[5], reverse=True)
for i,(label,tm,em,tkm,cost,total) in enumerate(scored,1):
    bar = '█' * int(total * 40)
    print(f'{i:2d}. {label:12s} {bar} {total:.3f}')

# 2. 费用对比条（对数尺度）
print(f"\n═══ 单次任务费用 ═══\n")
max_cost = max(r[4] for r in rows)
for label,tm,em,tkm,cost,ctx in sorted(rows, key=lambda x: x[4]):
    bar_len = max(1, int(cost / max_cost * 50))
    bar = '█' * bar_len
    print(f'{label:12s} ¥{cost:<8} {bar}')

# 3. 速度对比条
print(f"\n═══ 任务耗时 ═══\n")
max_time = max(r[2] for r in rows)
for label,tm,em,tkm,cost,ctx in sorted(rows, key=lambda x: x[2]):
    bar_len = max(1, int(em / max_time * 50))
    bar = '█' * bar_len
    print(f'{label:12s} {em:4.0f}s   {bar}')

# 4. 效率散点图 (费用 × 耗时)
print(f"\n═══ 费用效率分布 ═══\n")
print(f"  快↑")
print(f"    │")
# Build a 20x40 grid
grid = [[' ' for _ in range(50)] for _ in range(20)]
for label,tm,em,tkm,cost,ctx in rows:
    x = min(49, int(cost / max_cost * 49))
    y = min(19, int((1 - em / max_time) * 19))
    for ci, ch in enumerate(label[:8]):
        if x+ci < 50:
            grid[y][x+ci] = ch
for y in range(19, -1, -1):
    print(f'    │{"".join(grid[y])}')
print(f'  便宜└{"─"*49}贵→')

# 5. 数据表
print(f"\n═══ 完整数据 ═══\n")
print(f'{"模型":14s} {"回合":>4s} {"耗时":>6s} {"Token":>8s} {"€/t":>6s} {"s/t":>5s} {"费用":>8s} {"综合":>6s}')
print('-' * 65)
for label,tm,em,tkm,cost,total in scored:
    tpt = f'{tkm/tm:,.0f}' if tm > 0 else '-'
    ept = f'{em/tm:.1f}' if tm > 0 else '-'
    print(f'{label:14s} {tm:4.0f} {em:5.0f}s  {tkm:>8,.0f} {tpt:>6s} {ept:>5s} ¥{cost:<7} {total:.3f}')
