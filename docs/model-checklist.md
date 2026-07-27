# 新模型接入检查清单

向 `run_bench.py` 添加新模型前，逐个回答：

- [ ] 默认 thinking 级别: ______
- [ ] thinking 控制参数: `reasoning_effort` / `thinking.type` / `effort` / 其他 ______
- [ ] 最高档: ______
- [ ] 脚本 agent_loop.py 中的设置: ______ (必须等于最高档)
- [ ] 特殊约束（如 temperature=1、thinking 不可关闭）: ______

## 已接入模型状态

| 模型 | 默认 | 参数 | 最高 | 脚本设了 | 一致？ |
|------|:---:|------|:---:|:---:|:---:|
| DS V4 Pro | high | `reasoning_effort` | max | max | ✅ |
| DS V4 Flash | high | `reasoning_effort` | max | max | ✅ |
| Kimi K3 | max | `reasoning_effort` | max | max | ✅ |
| GLM 5.2 | max | `reasoning_effort` | max | max | ✅ |
| MiniMax M3 | **off** | `thinking.type` | adaptive | **adaptive** | ✅ |
| Grok 4.5 | high | `reasoning_effort` | high | high | ✅ |
| Claude Opus 5 | high | `effort` (Anthropic) | max | — | ⏳ |
