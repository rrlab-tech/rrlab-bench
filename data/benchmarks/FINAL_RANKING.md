# RRLabBench — 最终综合排名

> 评测时间: 2026-07-26 ~ 2026-07-27  
> 配置: 3 场景 × 8 模型配置 × n=1~3  
> 所有模型 thinking max（Opus 5 另测 medium）  
> 权重: 费用 30% + 耗时 30% + 回合 20% + Token 20%

## 最终排名

| 排名 | 模型 | 回合 | 耗时 | Token | 费用 | 综合 |
|:---:|------|:---:|:---:|:---:|:---:|:---:|
| 🥇 | **Grok 4.5** | 6 | 23s | 19K | ¥0.31 | **0.772** |
| 🥈 | **DS Flash** | 14 | 39s | 71K | ¥cli.07 | **0.615** |
| 🥉 | **DS Pro** | 12 | 49s | 53K | ¥0.17 | **0.447** |
| 4 | MiniMax M3 | 12 | 72s | 59K | ¥0.15 | **0.410** |
| 5 | GLM 5.2 | 10 | 84s | 34K | ¥0.30 | **0.387** |
| 6 | Opus 4.8 | 7 | 81s | 35K | ¥1.98 | **0.377** |
| 7 | Kimi K3 | 10 | 124s | 45K | ¥1.17 | **0.280** |
| 8 | Opus 5 MEDIUM | 12 | 77s | 73K | ¥3.19 | **0.248** |
| 9 | Opus 5 MAX | 21 | 226s | 228K | ¥9.94 | **0.106** |

## 详细场景数据

| 场景 | 模型 | FRR | 回合 | 耗时 | Token | 费用 | n |
|------|------|:---:|:---:|:---:|:---:|:---:|:---:|
| refactor-api | DS Pro | 0% | 12 | 43s | 52,976 | ¥0.17 | 3 |
| refactor-api | DS Flash | 0% | 14 | 32s | 62,328 | ¥0.07 | 3 |
| refactor-api | Kimi K3 | 0% | 10 | 99s | 40,132 | ¥1.02 | 3 |
| refactor-api | GLM 5.2 | 0% | 10 | 52s | 34,094 | ¥0.27 | 3 |
| refactor-api | MiniMax M3 | 0% | 10 | 49s | 35,352 | ¥0.09 | 3 |
| refactor-api | Grok 4.5 | 0% | 7 | 24s | 24,817 | ¥0.39 | 3 |
| refactor-api | Opus 5 M | 0% | 15 | 103s | 77,274 | ¥3.36 | 1 |
| refactor-api | Opus 5 MAX | 0% | 21 | 168s | 185,315 | ¥7.89 | 1 |
| refactor-api | Opus 4.8 | 0% | 14 | 128s | 111,657 | ¥5.22 | 1 |
| fix-bug-cascade | DS Pro | 0% | 15 | 59s | 63,433 | ¥0.21 | 3 |
| fix-bug-cascade | DS Flash | 0% | 15 | 41s | 84,593 | ¥0.09 | 3 |
| fix-bug-cascade | Kimi K3 | 0% | 9 | 121s | 41,064 | ¥1.08 | 3 |
| fix-bug-cascade | GLM 5.2 | 0% | 10 | 93s | 33,863 | ¥0.29 | 3 |
| fix-bug-cascade | MiniMax M3 | 0% | 14 | 63s | 59,811 | ¥0.15 | 3 |
| fix-bug-cascade | Grok 4.5 | 0% | 7 | 24s | 18,030 | ¥0.29 | 3 |
| fix-bug-cascade | Opus 5 M | 0% | 12 | 77s | 73,023 | ¥3.18 | 1 |
| fix-bug-cascade | Opus 5 MAX | 0% | 21 | 260s | 299,224 | ¥13.24 | 1 |
| fix-bug-cascade | Opus 4.8 | 0% | 7 | 81s | 34,908 | ¥1.98 | 1 |
| add-validation | DS Pro | 0% | 9 | 60s | 53,060 | ¥0.17 | 3 |
| add-validation | DS Flash | 0% | 12 | 45s | 79,917 | ¥0.08 | 3 |
| add-validation | Kimi K3 | 0% | 11 | 215s | 70,506 | ¥1.97 | 3 |
| add-validation | GLM 5.2 | 0% | 9 | 116s | 44,438 | ¥0.41 | 3 |
| add-validation | MiniMax M3 | 0% | 13 | 110s | 81,250 | ¥0.21 | 3 |
| add-validation | Grok 4.5 | 0% | 6 | 22s | 19,141 | ¥0.30 | 3 |
| add-validation | Opus 5 M | 0% | 10 | 72s | 56,906 | ¥2.61 | 1 |
| add-validation | Opus 5 MAX | 0% | 21 | 226s | 228,375 | ¥9.94 | 1 |
| add-validation | Opus 4.8 | 0% | 4 | 62s | 15,769 | ¥1.23 | 1 |

## 关键发现

1. **Grok 4.5 三维第一**: 最少回合、最少 Token、最快
2. **DS Flash 性价比无敌**: 最便宜，第二快
3. **Opus 5 MAX 严重过思考**: 21 回合 226s ¥10，降到 MEDIUM 后费用降 70%
4. **Kimi K3 垫底**: 比 DS Flash 贵 16 倍、慢 3 倍
5. **质量无差异**: 所有模型 FRR=0%，区分度全在效率维度
