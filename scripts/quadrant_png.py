#!/usr/bin/env python3
"""生成象限图 PNG — 需要 matplotlib"""
import json, sys, os
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("需要安装 matplotlib: pip install matplotlib")
    sys.exit(1)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "charts"
OUT_DIR.mkdir(exist_ok=True)

# 中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti SC', 'PingFang SC', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

MODELS = [
    ('deepseek-v4-pro', 'DS Pro', 3, 6),
    ('deepseek-v4-flash', 'DS Flash', 1, 2),
    ('kimi-k3', 'K3 (low)', 20, 100),
    ('glm-5.2', 'GLM 5.2', 7, 22),
    ('MiniMax-M3', 'MiniMax M3', 2.18, 8.7),
    ('x-ai/grok-4.5', 'Grok 4.5', 14.5, 43.5),
    ('anthropic/claude-opus-4.8', 'Opus 4.8', 36.25, 181.25),
]
SCENARIOS = ['refactor-api','fix-bug-cascade','add-validation']

def med(v):
    s=sorted(v); n=len(s)
    return s[n//2] if n%2==1 else (s[n//2-1]+s[n//2])/2

# 收集数据
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

# Opus 5 M & MAX
for suffix, label in [('', 'Opus5-Medium'), ('_max', 'Opus5-MAX')]:
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

# Kimi K3 thinking=max（归档数据，用于对比）
ARCHIVE_DIR = DATA_DIR / 'archive-20260726-openrouter'
all_t,all_e,all_tok,all_pt,all_ct = [],[],[],[],[]
for s in SCENARIOS:
    f = ARCHIVE_DIR / f"{s}_kimi-k3.json"
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
    rows.append(('K3 (max)', med(all_t), med(all_e), med(all_tok), med(all_pt), med(all_ct), 20, 100))

data = []
for label,tm,em,tkm,pm,cm,pi,po in rows:
    data.append({'label':label,'turns':tm,'time':em,'tokens':tkm,
                 'cost':pm/1e6*pi + cm/1e6*po,
                 'tpt':tkm/tm, 'ept':em/tm})

colors = ['#2ecc71','#3498db','#9b59b6','#e74c3c','#f39c12','#00bcd4','#ff6f00','#607d8b','#795548','#9b59b6']

# ═══════ 图 1: 费用 × 速度 象限图 ═══════
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_xlabel('单次任务费用 (¥)', fontsize=12)
ax.set_ylabel('任务耗时 (s)', fontsize=12)
ax.set_title('RRLabBench — Agent 效率象限: 费用 × 速度', fontsize=14, fontweight='bold')

# 象限分割线
cost_median = sorted(d['cost'] for d in data)[len(data)//2]
time_median = sorted(d['time'] for d in data)[len(data)//2]
ax.axvline(cost_median, color='gray', linestyle='--', alpha=0.5)
ax.axhline(time_median, color='gray', linestyle='--', alpha=0.5)

# 象限标签
ax.text(max(d['cost'] for d in data)*0.55, min(d['time'] for d in data)*1.1, 'Fast + Cheap  [BEST]', fontsize=11, color='green')
ax.text(max(d['cost'] for d in data)*0.55, max(d['time'] for d in data)*0.55, 'Slow + Expensive', fontsize=11, color='red')
ax.text(cost_median*0.4, max(d['time'] for d in data)*0.55, 'Slow + Cheap', fontsize=11, color='orange')
ax.text(cost_median*0.4, min(d['time'] for d in data)*1.1, 'Fast + Expensive', fontsize=11, color='gray', alpha=0.3)

for i, d in enumerate(data):
    ax.scatter(d['cost'], d['time'], s=d['tokens']/800, c=colors[i], edgecolors='white', linewidth=2, zorder=5)
    offset_x = d['cost'] * 0.02
    offset_y = -3 if d['label'] == 'Grok 4.5' else 5
    ax.annotate(f"{d['label']}\n¥{d['cost']:.2f} {d['time']:.0f}s",
                (d['cost'], d['time']), textcoords="offset points", xytext=(10, offset_y),
                fontsize=9, fontweight='bold')

# K3 max → low 迁移箭头
k3_max = next((d for d in data if d['label'] == 'K3 (max)'), None)
k3_low = next((d for d in data if d['label'] == 'K3 (low)'), None)
if k3_max and k3_low:
    ax.annotate('', xy=(k3_low['cost'], k3_low['time']), xytext=(k3_max['cost'], k3_max['time']),
                arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2.5, linestyle='--'))

# 图例: 气泡大小 = Token
legend_labels = ['20K', '50K', '100K', '200K']
legend_sizes = [20000/800, 50000/800, 100000/800, 200000/800]
legend_handles = [plt.scatter([],[], s=s, c='gray', alpha=0.3, edgecolors='white', linewidth=1) for s in legend_sizes]
ax.legend(legend_handles, legend_labels, title='Token 量', loc='lower right', framealpha=0.9)

ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig(OUT_DIR / 'quadrant_cost_speed.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {OUT_DIR / 'quadrant_cost_speed.png'}")

# ═══════ 图 2: 费用 × 回合 气泡图 ═══════
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_xlabel('单次任务费用 (¥)', fontsize=12)
ax.set_ylabel('回合数', fontsize=12)
ax.set_title('RRLabBench — 费用 × 回合 (气泡=Token量)', fontsize=14, fontweight='bold')

turn_median = sorted(d['turns'] for d in data)[len(data)//2]
ax.axvline(cost_median, color='gray', linestyle='--', alpha=0.5)
ax.axhline(turn_median, color='gray', linestyle='--', alpha=0.5)

for i, d in enumerate(data):
    ax.scatter(d['cost'], d['turns'], s=d['tokens']/600, c=colors[i], edgecolors='white', linewidth=2, zorder=5)
    # 手动调整重叠标签（全部向右偏移避免出界）
    offsets = {'MiniMax M3': (10,-12), 'DS Pro': (10,-5), 'Opus5-Medium': (10,8), 'GLM 5.2': (10,-10), 'Opus5-MAX': (10,-15)}
    ox, oy = offsets.get(d['label'], (10, 5))
    ax.annotate(f"{d['label']}", (d['cost'], d['turns']), textcoords="offset points", xytext=(ox, oy), fontsize=9, fontweight='bold')

ax.set_xlim(left=-0.1, right=max(d['cost'] for d in data)*1.15)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig(OUT_DIR / 'quadrant_cost_turns.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {OUT_DIR / 'quadrant_cost_turns.png'}")

# ═══════ 图 3: 综合排名横向条形图 ═══════
fig, ax = plt.subplots(figsize=(10, 7))

# 计算综合分（与 FINAL_RANKING.md 同口径：回合×0.4 + Token/1000×0.3 + 耗时×0.3，越低越好）
scored = []
for d in data:
    s = d['turns']*0.4 + d['tokens']/1000*0.3 + d['time']*0.3
    scored.append((d['label'], s))

scored.sort(key=lambda x: -x[1])  # 差分在上，好分在下
labels = [s[0] for s in scored]
scores = [s[1] for s in scored]
n = len(scored)
bar_colors = []
for i in range(n):
    rank = n - i  # 底部是第 1 名
    if rank <= 3: bar_colors.append('#2ecc71')
    elif rank <= 6: bar_colors.append('#f39c12')
    else: bar_colors.append('#e74c3c')

ax.barh(labels, scores, color=bar_colors, height=0.6)
ax.set_xlabel('综合效率分 (回合×0.4 + Token/1000×0.3 + 耗时×0.3，越低越好)', fontsize=11)
ax.set_title('RRLabBench — 综合排名（顶部为第 1 名）', fontsize=14, fontweight='bold')

for i, (label, score) in enumerate(scored):
    ax.text(score + 0.3, i, f'{score:.1f}', va='center', fontweight='bold')

ax.set_xlim(0, max(scores) * 1.12)
ax.grid(True, axis='x', alpha=0.2)
plt.tight_layout()
plt.savefig(OUT_DIR / 'ranking.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {OUT_DIR / 'ranking.png'}")

print(f"\n✅ 3 张图表已生成 → {OUT_DIR}/")
