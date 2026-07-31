# 优先序（v0.1 → v1.0）

> **并行方向**：Bench-Harness（测/进化 Harness 而非模型）已立项存档，见 [bench-harness-v0.1.md](bench-harness-v0.1.md)。中长期跟踪，独立于本 roadmap 推进。

## Phase 0: 方法论白皮书（当前 — 2 周）

- [ ] 完成方法论白皮书
- [ ] **白皮书发布前：GLM 5.2 用智谱官方直连重跑**（2026-07-28 起 cli.py/run_bench.py 已切换；REPORT.md 中现有 GLM 数据走 OpenRouter 中转，成本/耗时口径不一致，正式引用前需重测）
- [ ] 用 eVoiceClawBenchmark 现有数据做一次匿名化行业分布分析
- [ ] 作为第一篇公开文章发布

## Phase 1: 最小可用框架（2-6 周）

- [ ] DRI 评测引擎（单模型 × 单场景 × n≥10）
- [ ] 客户自部署模板（Docker Compose）
- [ ] 3 个预定义审计场景（代码修改、配置变更、依赖更新）
- [ ] 命令行工具：`rrlab-bench audit --model xxx --scenario xxx`
- [ ] 首批 2 个付费客户免费试用（换案例 + 换反馈）

## Phase 2: 回归监控（6-12 周）

- [ ] 定时调度器
- [ ] 基线建立 + 漂移检测
- [ ] 告警通知（钉钉/飞书/邮件）
- [ ] 单客户 ¥2-5k/月订阅

## Phase 3: FDE 深度审计（12 周+）

- [ ] 客户定制场景编写
- [ ] 审计报告模板（可交付给 CTO 的格式）
- [ ] ¥3-5 万/次 → 自然转化 FDE 落地 Sprint（¥10-50 万）
