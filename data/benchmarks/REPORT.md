# RRLabBench v0.3 — 批量评测报告

> 评测时间：2026-07-26 18:42–19:16 (33.8 min)  
> 配置：3 场景 × 4 模型 × 3 次 = 36 次完整 Agent 循环  
> 场景：refactor-api / fix-bug-cascade / add-validation  
> 指标：FRR（质量） / 回合 / 耗时 / Token / 费用
>
> **口径说明**：本报告中 GLM 5.2 数据经 OpenRouter 中转调用（非智谱官方 API）。
> 2026-07-28 起 cli.py 与 run_bench.py 均已切换至官方直连（open.bigmodel.cn + ZHIPU_API_KEY），
> 后续重跑数据与本报告 GLM 行的成本/耗时口径不完全可比。

---

## 原始数据

| 场景 | 模型 | 回合 | 耗时 | Token | 费用 |
|------|------|:---:|:---:|:---:|:---:|
| refactor-api | deepseek-v4-pro | 11 | 36s | 46,176 | ¥0.1454 |
| refactor-api | deepseek-v4-flash | 15 | 29s | 60,415 | ¥0.0629 |
| refactor-api | kimi-k3 | 9 | 52s | 21,294 | ¥0.5095 |
| refactor-api | glm-5.2 | 12 | 79s | 45,927 | ¥0.3624 |
| fix-bug-cascade | deepseek-v4-pro | 11 | 51s | 48,231 | ¥0.1528 |
| fix-bug-cascade | deepseek-v4-flash | 12 | 36s | 50,312 | ¥0.0533 |
| fix-bug-cascade | kimi-k3 | 6 | 35s | 10,823 | ¥0.2747 |
| fix-bug-cascade | glm-5.2 | 11 | 95s | 50,615 | ¥0.4085 |
| add-validation | deepseek-v4-pro | 8 | 45s | 40,748 | ¥0.1310 |
| add-validation | deepseek-v4-flash | 12 | 32s | 61,575 | ¥0.0643 |
| add-validation | kimi-k3 | 8 | 44s | 23,434 | ¥0.5392 |
| add-validation | glm-5.2 | 4 | 72s | 10,868 | ¥0.1395 |

## 汇总

| 模型 | 平均回合 | 平均耗时 | 平均 Token | 平均费用 | 质量 |
|------|:---:|:---:|:---:|:---:|:---:|
| DS V4 Pro | 10.0 | 44s | 45,052 | ¥0.14 | ✅ |
| DS V4 Flash | 13.0 | 32s | 57,434 | ¥0.06 | ✅ |
| Kimi K3 | 7.7 | 44s | 18,517 | ¥0.44 | ✅ |
| GLM 5.2 | 9.0 | 82s | 35,803 | ¥0.30 | ✅ |

## 结论

- **综合最佳**: DS V4 Pro（可靠、快速、价格可控）
- **性价比之王**: DS V4 Flash（最便宜、最快，但需验证大项目质量）
- **效率不差但不可持续**: Kimi K3（Token 少 51%，但费用高 3.7 倍）
- **不稳定**: GLM 5.2（简单任务快，复杂任务慢 2.5 倍）
