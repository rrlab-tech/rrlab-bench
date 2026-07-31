#!/usr/bin/env python3
"""K3 thinking=max vs thinking=low 对比图表"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "charts"
OUT_DIR.mkdir(exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti SC', 'PingFang SC', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

C_MAX = '#e74c3c'  # 红 = max
C_LOW = '#2ecc71'  # 绿 = low

# ═══════ 数据（中位数）═══════
scenarios = ['refactor-api', 'fix-bug-cascade', 'add-validation']
turns_max, turns_low = [10, 9, 11], [9, 6, 7]
time_max,  time_low  = [98.8, 120.7, 215.3], [62.6, 40.6, 85.0]
tok_max,   tok_low   = [40132, 41064, 70506], [19213, 10555, 20428]

# ═══════ 图 1: 按场景对比（3 子图）═══════
fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
fig.suptitle('Kimi K3: thinking=max vs thinking=low（按场景，中位数）', fontsize=15, fontweight='bold')

metrics = [
    ('轮次', turns_max, turns_low, '%d', [(-10,'-10%'),(-33,'-33%'),(-36,'-36%')]),
    ('耗时 (秒)', time_max, time_low, '%.0f', [(-37,'-37%'),(-66,'-66%'),(-61,'-61%')]),
    ('Token 消耗', tok_max, tok_low, '%.0f', [(-52,'-52%'),(-74,'-74%'),(-71,'-71%')]),
]

x = np.arange(3)
w = 0.35

for ax, (title, vmax, vlow, fmt, changes) in zip(axes, metrics):
    b1 = ax.bar(x - w/2, vmax, w, label='thinking=max', color=C_MAX, alpha=0.85)
    b2 = ax.bar(x + w/2, vlow, w, label='thinking=low', color=C_LOW, alpha=0.85)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['refactor-api', 'fix-bug\n-cascade', 'add-validation'], fontsize=10)
    ax.grid(True, axis='y', alpha=0.2)
    for i, (v1, v2, (_, pct)) in enumerate(zip(vmax, vlow, changes)):
        ax.text(i - w/2, v1*1.01, fmt % v1, ha='center', fontsize=9, fontweight='bold', color=C_MAX)
        ax.text(i + w/2, v2*1.01, fmt % v2, ha='center', fontsize=9, fontweight='bold', color='#1e8449')
        # 降幅标注（绿色，在 low 柱上方）
        ax.text(i + w/2, v2*1.01 + max(vmax)*0.06, pct, ha='center', fontsize=10,
                fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#27ae60', edgecolor='none'))
    ax.set_ylim(0, max(vmax) * 1.22)

axes[0].legend(loc='upper right', fontsize=10)
plt.tight_layout()
plt.savefig(OUT_DIR / 'k3_scenario_compare.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {OUT_DIR / 'k3_scenario_compare.png'}")

# ═══════ 图 2: 整体汇总（9 次总量）═══════
fig, axes = plt.subplots(1, 3, figsize=(13, 5))
fig.suptitle('Kimi K3: thinking=max vs thinking=low（9 次测试总量）', fontsize=15, fontweight='bold')

totals = [
    ('总轮次', 90, 66, '-27%'),
    ('总耗时 (秒)', 1385, 553, '-60%'),
    ('总 Token', 468028, 153740, '-67%'),
]

for ax, (title, v_max, v_low, pct) in zip(axes, totals):
    bars = ax.bar(['thinking=max', 'thinking=low'], [v_max, v_low],
                  color=[C_MAX, C_LOW], width=0.55, alpha=0.85)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.2)
    fmt = '{:,.0f}'
    ax.text(0, v_max*1.02, fmt.format(v_max), ha='center', fontsize=11, fontweight='bold', color=C_MAX)
    ax.text(1, v_low*1.02, fmt.format(v_low), ha='center', fontsize=11, fontweight='bold', color='#1e8449')
    ax.text(0.5, max(v_max, v_low)*0.55, pct, ha='center', fontsize=20, fontweight='bold',
            color='white', bbox=dict(boxstyle='round,pad=0.4', facecolor='#27ae60', edgecolor='none'))
    ax.set_ylim(0, v_max * 1.18)

plt.tight_layout()
plt.savefig(OUT_DIR / 'k3_overall_compare.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {OUT_DIR / 'k3_overall_compare.png'}")
