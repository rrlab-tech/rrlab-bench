import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# 数据
models = [
    "Grok 4.5", "DS Flash", "DS Pro", "MiniMax M3",
    "GLM 5.2", "Opus 4.8", "Kimi K3", "Opus 5"
]
costs = [0.31, 0.07, 0.17, 0.15, 0.30, 1.98, 1.17, 9.94]
turns = [6, 14, 12, 12, 10, 7, 10, 21]
times = [23, 39, 49, 72, 84, 81, 124, 226]
tokens = [19000, 71000, 53000, 59000, 34000, 35000, 45000, 228000]
scores = [0.772, 0.615, 0.447, 0.410, 0.387, 0.377, 0.280, 0.106]

# 按费用升序排列
sorted_idx = np.argsort(costs)

# 字体
font_path = '/System/Library/Fonts/STHeiti Light.ttc'
prop = fm.FontProperties(fname=font_path)

fig, axes = plt.subplots(1, 3, figsize=(16, 6), facecolor='white')
colors = ['#2563eb' if c >= 1.0 else '#10b981' for c in costs]

# --- 图1: 费用对比 (水平柱状图) ---
ax = axes[0]
y_pos = range(len(models))
sorted_costs = [costs[i] for i in sorted_idx]
sorted_labels = [models[i] for i in sorted_idx]
sorted_colors = [colors[i] for i in sorted_idx]

bars = ax.barh(y_pos, sorted_costs, height=0.6, color=sorted_colors, edgecolor='white', linewidth=0.5)
for i, (bar, val) in enumerate(zip(bars, sorted_costs)):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f'¥{val:.2f}', va='center', fontsize=10, fontproperties=prop,
            color='#374151')

ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_labels, fontproperties=prop, fontsize=10)
ax.set_xlabel('费用 / 次 (¥)', fontproperties=prop, fontsize=11)
ax.set_title('单次任务费用对比', fontproperties=prop, fontsize=13, fontweight='bold')
ax.set_xlim(0, max(sorted_costs) * 1.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='x', labelsize=9)

# --- 图2: 耗时 + 回合 (散点图, 气泡大小=Token) ---
ax = axes[1]
scatter = ax.scatter(times, turns, s=[t/500 for t in tokens], c=range(len(models)),
                     cmap='viridis', alpha=0.7, edgecolors='white', linewidth=1)
for i, model in enumerate(models):
    offset_y = 0.5 if i not in [0, 3, 5] else -0.8
    ax.annotate(model, (times[i], turns[i]),
                textcoords="offset points", xytext=(0, offset_y * 12),
                fontsize=8, fontproperties=prop, ha='center', color='#374151')

ax.set_xlabel('耗时 (秒)', fontproperties=prop, fontsize=11)
ax.set_ylabel('回合数', fontproperties=prop, fontsize=11)
ax.set_title('耗时 vs 回合 (气泡=Token 消耗)', fontproperties=prop, fontsize=13, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# --- 图3: 综合评分 (水平柱状图) ---
ax = axes[2]
sorted_scores = [scores[i] for i in sorted_idx]

bars = ax.barh(y_pos, sorted_scores, height=0.6, color='#6366f1', edgecolor='white', linewidth=0.5)
for i, (bar, val) in enumerate(zip(bars, sorted_scores)):
    ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
            f'{val:.3f}', va='center', fontsize=10, color='#374151')

ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_labels, fontproperties=prop, fontsize=10)
ax.set_xlabel('综合评分', fontproperties=prop, fontsize=11)
ax.set_title('综合效率评分\n(费用30% + 耗时30% + 回合20% + Token20%)', fontproperties=prop, fontsize=13, fontweight='bold')
ax.set_xlim(0, max(sorted_scores) * 1.2)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='x', labelsize=9)

plt.tight_layout(pad=2)
plt.savefig('/Volumes/Other/Agent/rrlab/rrlab-bench/charts/model_efficiency_comparison.png',
            dpi=200, bbox_inches='tight', facecolor='white')
print("Saved to charts/model_efficiency_comparison.png")
