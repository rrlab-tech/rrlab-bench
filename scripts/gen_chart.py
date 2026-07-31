#!/usr/bin/env python3
"""生成模型综合对比图 — 动态从 data/*.json 读取"""
import json, os
from pathlib import Path
from statistics import median

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np
except ImportError:
    print("需要安装: pip install matplotlib numpy")
    exit(1)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "charts"
OUT_DIR.mkdir(exist_ok=True)

MODELS = [
    ("deepseek-v4-pro", "DS Pro", 3.0, 6.0),
    ("deepseek-v4-flash", "DS Flash", 1.0, 2.0),
    ("kimi-k3", "Kimi K3", 20.0, 100.0),
    ("glm-5.2", "GLM 5.2", 7.0, 22.0),
    ("MiniMax-M3", "MiniMax M3", 2.18, 8.7),
    ("x-ai/grok-4.5", "Grok 4.5", 14.5, 43.5),
    ("anthropic/claude-opus-4.8", "Opus 4.8", 36.25, 181.25),
    ("anthropic/claude-opus-5", "Opus 5", 36.25, 181.25),
    ("anthropic/claude-opus-5_max", "Opus MAX", 36.25, 181.25),
    ("openai/gpt-5.6-luna", "GPT Luna", 0.73, 4.38),
]
SCENARIOS = ["refactor-api", "fix-bug-cascade", "add-validation"]

# 字体
font_paths = [
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
]
font_path = next((p for p in font_paths if os.path.exists(p)), None)
if font_path:
    prop = fm.FontProperties(fname=font_path)
else:
    prop = fm.FontProperties()

# 收集数据
rows = []
for slug, label, iprice, oprice in MODELS:
    file_slug = slug.replace("/", "_")
    runs = []
    for sc in SCENARIOS:
        f = DATA_DIR / f"{sc}_{file_slug}.json"
        try:
            d = json.loads(f.read_text())
            results = d if isinstance(d, list) else d.get("results", [])
            runs.extend([r for r in results if r and not r.get("error")])
        except Exception:
            pass
    if not runs:
        continue

    turn = int(median(r["turns"] for r in runs))
    time = int(median(r["elapsed"] for r in runs))
    tok = int(median(r["total_tokens"] for r in runs))
    ptok = int(median(r.get("prompt_tokens", tok // 2) for r in runs))
    ctok = int(median(r.get("completion_tokens", tok // 2) for r in runs))
    cost = round(ptok / 1e6 * iprice + ctok / 1e6 * oprice, 4)
    rows.append((label, cost, turn, time, tok, len(runs)))

# 归一化评分 (所有指标越低越好，归一化后 1-best, 0-worst)
def norm(vals, invert=True):
    mn, mx = min(vals), max(vals)
    if mx == mn:
        return [1.0] * len(vals)
    n = [(v - mn) / (mx - mn) for v in vals]
    return [1.0 - x if invert else x for x in n]

labels = [r[0] for r in rows]
costs = [r[1] for r in rows]
turns = [r[2] for r in rows]
times = [r[3] for r in rows]
tokens = [r[4] for r in rows]
counts = [r[5] for r in rows]

# 综合评分: 费用30% + 耗时30% + 回合20% + Token20%
n_cost = norm(costs)
n_time = norm(times)
n_turn = norm(turns)
n_tok = norm(tokens)
scores = [c * 0.3 + t * 0.3 + u * 0.2 + k * 0.2 for c, t, u, k in zip(n_cost, n_time, n_turn, n_tok)]

# 按费用排序
sorted_idx = np.argsort(costs)

# --- 画图 ---
fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor='white')

# 颜色: 贵=蓝, 便宜=绿
colors = ['#2563eb' if c >= 0.5 else '#10b981' for c in costs]

# 图1: 费用对比
ax = axes[0]
y_pos = range(len(rows))
sorted_costs = [costs[i] for i in sorted_idx]
sorted_labels = [labels[i] for i in sorted_idx]
sorted_colors = [colors[i] for i in sorted_idx]

bars = ax.barh(y_pos, sorted_costs, height=0.6, color=sorted_colors, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, sorted_costs):
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
            f'¥{val:.4f}', va='center', fontsize=10, fontproperties=prop, color='#374151')
ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_labels, fontproperties=prop, fontsize=10)
ax.set_xlabel('费用 / 次 (¥)', fontproperties=prop, fontsize=11)
ax.set_title('单次任务费用对比', fontproperties=prop, fontsize=13, fontweight='bold')
ax.set_xlim(0, max(sorted_costs) * 1.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 图2: 耗时 vs 回合 (气泡大小 = Token)
ax = axes[1]
scatter = ax.scatter(times, turns, s=[t / 300 for t in tokens], c=range(len(rows)),
                     cmap='plasma', alpha=0.75, edgecolors='white', linewidth=1)
for i, label in enumerate(labels):
    offset_y = 0.8 if i not in [0, 2, 4, 5] else -0.8
    ax.annotate(label, (times[i], turns[i]),
                textcoords="offset points", xytext=(0, offset_y * 10),
                fontsize=8, fontproperties=prop, ha='center', color='#374151')
ax.set_xlabel('耗时 (秒)', fontproperties=prop, fontsize=11)
ax.set_ylabel('回合数', fontproperties=prop, fontsize=11)
ax.set_title('耗时 vs 回合 (气泡=Token 消耗)', fontproperties=prop, fontsize=13, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 图3: 综合评分
ax = axes[2]
sorted_scores = [scores[i] for i in sorted_idx]

bars = ax.barh(y_pos, sorted_scores, height=0.6, color='#6366f1', edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, sorted_scores):
    ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
            f'{val:.3f}', va='center', fontsize=10, color='#374151')
ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_labels, fontproperties=prop, fontsize=10)
ax.set_xlabel('综合评分', fontproperties=prop, fontsize=11)
ax.set_title('综合效率评分\n(费用30% + 耗时30% + 回合20% + Token20%)', fontproperties=prop, fontsize=13, fontweight='bold')
ax.set_xlim(0, max(sorted_scores) * 1.15)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout(pad=2)
out = OUT_DIR / "model_efficiency_comparison.png"
plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
print(f"✅ {out}")
