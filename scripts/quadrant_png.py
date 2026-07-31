#!/usr/bin/env python3
"""Generate quadrant & ranking charts for RRLabBench"""
import json, sys, os
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("Need: pip install matplotlib")
    sys.exit(1)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "charts"
OUT_DIR.mkdir(exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

MODELS = [
    ('deepseek-v4-pro',       'DS V4 Pro',   3.0,  6.0),
    ('deepseek-v4-flash',     'DS V4 Flash', 1.0,  2.0),
    ('kimi-k3',               'Kimi K3 (low)',20.0, 100.0),
    ('glm-5.2',               'GLM 5.2',     7.0,  22.0),
    ('MiniMax-M3',            'MiniMax M3',  2.18, 8.7),
    ('x-ai/grok-4.5',         'Grok 4.5',    14.5, 43.5),
    ('anthropic/claude-opus-4.8', 'Opus 4.8', 36.25, 181.25),
    ('anthropic/claude-opus-5',   'Opus 5',   36.25, 181.25),
    ('openai/gpt-5.6-luna',   'GPT Luna',    0.73, 4.38),
]
SCENARIOS = ['refactor-api','fix-bug-cascade','add-validation']

COLORS = ['#2ecc71','#3498db','#9b59b6','#e74c3c','#f39c12',
          '#00bcd4','#ff6f00','#607d8b','#e91e63','#4caf50',
          '#ff5722','#2196f3','#9c27b0']

def med(v):
    s = sorted(v); n = len(s)
    return s[n//2] if n%2==1 else (s[n//2-1]+s[n//2])/2

# ── Collect data ──
rows = []
for mid, label, pi, po in MODELS:
    at, ae, atok, apt, act = [], [], [], [], []
    for s in SCENARIOS:
        f = DATA_DIR / f"{s}_{mid.replace('/', '_')}.json"
        try:
            d = json.loads(f.read_text())
            results = d if isinstance(d, list) else d.get('results', [])
            valid = [r for r in results if r and r.get('error') is None]
            if valid:
                at   += [r['turns'] for r in valid]
                ae   += [r['elapsed'] for r in valid]
                atok += [r['total_tokens'] for r in valid]
                apt  += [r.get('prompt_tokens', 0) for r in valid]
                act  += [r.get('completion_tokens', 0) for r in valid]
        except:
            pass
    if at:
        rows.append((label, med(at), med(ae), med(atok), med(apt), med(act), pi, po))

# Kimi K3 thinking=max (archived, for comparison)
ARCHIVE = DATA_DIR / 'archive-20260726-openrouter'
at2, ae2, atok2, apt2, act2 = [], [], [], [], []
for s in SCENARIOS:
    f = ARCHIVE / f"{s}_kimi-k3.json"
    try:
        d = json.loads(f.read_text())
        results = d if isinstance(d, list) else d.get('results', [])
        valid = [r for r in results if r and r.get('error') is None]
        if valid:
            at2   += [r['turns'] for r in valid]
            ae2   += [r['elapsed'] for r in valid]
            atok2 += [r['total_tokens'] for r in valid]
            apt2  += [r.get('prompt_tokens', 0) for r in valid]
            act2  += [r.get('completion_tokens', 0) for r in valid]
    except:
        pass
if at2:
    rows.append(('K3 (max)', med(at2), med(ae2), med(atok2), med(apt2), med(act2), 20, 100))

# Build data list
data = []
for label, tm, em, tkm, pm, cm, pi, po in rows:
    data.append({
        'label': label, 'turns': tm, 'time': em, 'tokens': tkm,
        'cost': pm/1e6*pi + cm/1e6*po,
        'tpt': tkm/max(tm,1), 'ept': em/max(tm,1)
    })

# Color legend patches (one per model, from MODELS + archive K3 max)
model_colors = {}
for i, row in enumerate(rows):
    model_colors[row[0]] = COLORS[i % len(COLORS)]

# ═══════════════════════════════════════════════════════════
# Chart 1: Cost × Speed Quadrant
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 9))

cost_med = sorted(d['cost'] for d in data)[len(data)//2]
time_med = sorted(d['time'] for d in data)[len(data)//2]
ax.axvline(cost_med, color='gray', linestyle='--', alpha=0.4)
ax.axhline(time_med, color='gray', linestyle='--', alpha=0.4)

ax.set_xlabel('Cost per Task (¥)', fontsize=12)
ax.set_ylabel('Task Time (seconds)', fontsize=12)
ax.set_title('RRLabBench — Agent Efficiency Quadrant: Cost × Speed', fontsize=14, fontweight='bold')

# Quadrant labels
x_r = max(d['cost'] for d in data)
y_t = max(d['time'] for d in data)
ax.text(x_r*0.55, y_t*0.06, 'Fast + Cheap  ← BEST', fontsize=11, color='#16a34a', fontweight='bold')
ax.text(x_r*0.55, y_t*0.88, 'Slow + Expensive', fontsize=11, color='#dc2626')
ax.text(x_r*0.02, y_t*0.88, 'Slow + Cheap', fontsize=11, color='#d97706')
ax.text(x_r*0.02, y_t*0.06, 'Fast + Expensive', fontsize=11, color='#9ca3af')

for i, d in enumerate(data):
    c = COLORS[i % len(COLORS)]
    ax.scatter(d['cost'], d['time'], s=d['tokens']/800, c=c,
               edgecolors='white', linewidth=2, zorder=5)
    dy = -5 if d['label'] == 'Grok 4.5' else 6
    ax.annotate(d['label'], (d['cost'], d['time']),
                textcoords="offset points", xytext=(10, dy),
                fontsize=9, fontweight='bold')

# K3 migration arrow
k3_max = next((d for d in data if d['label'] == 'K3 (max)'), None)
k3_low = next((d for d in data if d['label'] == 'K3 (low)'), None)
if k3_max and k3_low:
    ax.annotate('', xy=(k3_low['cost'], k3_low['time']),
                xytext=(k3_max['cost'], k3_max['time']),
                arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2.5, linestyle='--'))
    ax.text((k3_max['cost']+k3_low['cost'])/2, (k3_max['time']+k3_low['time'])/2+8,
            'think=low', fontsize=8, color='#9b59b6', fontstyle='italic')

# Legend: model colors
ax.legend(handles=[mpatches.Patch(color=model_colors[l], label=l)
                    for l in [r[0] for r in rows]],
          title='Models', loc='lower right',
          framealpha=0.9, fontsize=8, title_fontsize=10, ncol=2)

ax.set_xlim(left=-0.01)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.15)
plt.tight_layout()
plt.savefig(OUT_DIR / 'quadrant_cost_speed.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"OK {OUT_DIR / 'quadrant_cost_speed.png'}")

# ═══════════════════════════════════════════════════════════
# Chart 2: Cost × Turns Bubble
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 9))

turn_med = sorted(d['turns'] for d in data)[len(data)//2]
ax.axvline(cost_med, color='gray', linestyle='--', alpha=0.4)
ax.axhline(turn_med, color='gray', linestyle='--', alpha=0.4)

ax.set_xlabel('Cost per Task (¥)', fontsize=12)
ax.set_ylabel('Turns', fontsize=12)
ax.set_title('RRLabBench — Cost × Turns (bubble = token volume)', fontsize=14, fontweight='bold')

for i, d in enumerate(data):
    c = COLORS[i % len(COLORS)]
    ax.scatter(d['cost'], d['turns'], s=d['tokens']/600, c=c,
               edgecolors='white', linewidth=2, zorder=5)
    ox = 10
    oy = -10 if d['label'] in ('MiniMax M3', 'GLM 5.2') else 6
    ax.annotate(d['label'], (d['cost'], d['turns']),
                textcoords="offset points", xytext=(ox, oy),
                fontsize=9, fontweight='bold')

# Model legend
ax.legend(handles=[mpatches.Patch(color=model_colors[l], label=l)
                    for l in [r[0] for r in rows]],
          title='Models', loc='lower right',
          framealpha=0.9, fontsize=8, title_fontsize=10, ncol=2)

ax.set_xlim(left=-0.01)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.15)
plt.tight_layout()
plt.savefig(OUT_DIR / 'quadrant_cost_turns.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"OK {OUT_DIR / 'quadrant_cost_turns.png'}")

# ═══════════════════════════════════════════════════════════
# Chart 3: Composite Ranking Bar
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 7))

# Deduplicate: exclude K3(max) from ranking, keep K3(low)
rank_data = [d for d in data if d['label'] != 'K3 (max)']
scored = [(d['label'], d['turns']*0.4 + d['tokens']/1000*0.3 + d['time']*0.3)
          for d in rank_data]
scored.sort(key=lambda x: -x[1])  # worst at top
labels = [s[0] for s in scored]
scores = [s[1] for s in scored]
n = len(scored)

bar_colors = []
for i in range(n):
    rank = n - i
    if rank <= 3:    bar_colors.append('#2ecc71')
    elif rank <= 6:  bar_colors.append('#f39c12')
    else:            bar_colors.append('#e74c3c')

ax.barh(labels, scores, color=bar_colors, height=0.6)
ax.set_xlabel('Efficiency Score (lower = better)\n'
              'turns×0.4 + tokens/1000×0.3 + time×0.3', fontsize=11)
ax.set_title('RRLabBench — Composite Ranking (#1 at top)', fontsize=14, fontweight='bold')

for i, (label, score) in enumerate(scored):
    ax.text(score + 0.3, i, f'{score:.1f}', va='center', fontweight='bold')

ax.set_xlim(0, max(scores) * 1.12)
ax.grid(True, axis='x', alpha=0.15)
plt.tight_layout()
plt.savefig(OUT_DIR / 'ranking.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"OK {OUT_DIR / 'ranking.png'}")

print(f"\nDone → {OUT_DIR}/")
