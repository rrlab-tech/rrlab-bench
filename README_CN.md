# RRLabBench

> 模型的排行并不能代表被使用时的最终能力

[English](README.md) | 中文

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

## 这是什么

RRLabBench 是一套 **Agent 代码修改能力的审计工具**。它不排名模型，而是回答两个工程问题：

1. **回归风险 (FRR)**：模型改完代码后，原本通过的测试还过吗？
2. **效率差异**：同等质量下，哪些模型更快、更省 Token、更便宜？

### 为什么需要这个

现有的LLM排行榜都在告诉我们「哪个模型最聪明」。但正如那些被称为“死读书”的学生一样，考试考得好不代表真的能在实践工作中表现出色。而作为大语言模型，其最终的存在意义和价值是在实际使用过程中表现。RRLabBench 告诉你「哪个模型最适合你的 Agent 工作流」—— 这里包括了：模型解决问题的轮回次数、解决问题所需要的时间、解决问题花飞多少Token等。这些是实际用户承担的成本。

### 实际使用中体现出来的差距

我们审计了 9 个模型，发现了三个反直觉的事实：

**1. 参数规模 ≠ Agent 效率**

所有模型在正确率上没有差异（FRR 全部 0%）。但做同一件事的成本天差地别：最快的模型只使用了6个回合，总计花了23秒，花费¥0.31；最慢的使用了21个回合。花了226秒和¥9.94——**32 倍的差价，但产出完全一样。**

**2. 深度思考在 Agent 场景是负资产**

MAX思考档的Opus 5表现出了「过度自我验证」——反复检查、冗长的内部推理，最终和 MEDIUM 档的结果没有区别，但费用高了3倍。在考试里深度思考是优势，在 Agent 里每一轮过度思考都是用户的钱和时间。

**3. 用户真的可以借助这些排行来选择模型吗**

排行榜在前的模型，实际使用下来并不理想。这体现了什么？模型为了排行榜多了优化？实际并没有考虑更多用户的使用感受？只为尽快回收成本而过度消耗和输出Token。

> 模型无论其在专业测评中的能力如何，其最终目的还是为了被使用。

## 快速开始

### 安装

```bash
# 从 GitHub
git clone https://github.com/rrlab-tech/rrlab-bench.git
cd rrlab-bench
pip install -e .
```

### 设置 API Key

```bash
# DeepSeek
export DEEPSEEK_API_KEY=sk-xxx

# OpenRouter (Claude, GLM, MiniMax, Grok 等)
export OPENROUTER_API_KEY=sk-or-v1-xxx

# Kimi
export KIMI_API_KEY=sk-xxx
```

### 运行

```bash
# 单个场景
rrlab-bench audit --model deepseek-v4-pro --scenario refactor-api --runs 3

# 全部三场景
rrlab-bench audit --model deepseek-v4-pro --all-scenarios --runs 3

# 快速测试（别名）
rrlab-bench run --model kimi-k3 --all-scenarios
```

### 输出示例

```
🔬 RRLabBench v0.3 | refactor-api | deepseek-v4-pro ×3
   [1/3] ✅ FRR=0% turn=12 43.2s ¥0.17
   [2/3] ✅ FRR=0% turn=12 51.0s ¥0.17
   [3/3] ✅ FRR=0% turn=12 54.3s ¥0.18

📊 汇总 (3/3 次成功)
   FRR 中位数:    0.0%
   代码崩溃:      0/3
   平均回合:      12.0
   平均耗时:      49.5s
   平均 Token:    53,000
   平均费用:      ¥0.17
```

## 场景说明

三个测试场景，覆盖真实 Agent 编程任务的常见风险：

| 场景 | 描述 | 难度 |
|------|------|:---:|
| `refactor-api` | 改方法签名 → 三个调用点全挂 | 中 |
| `fix-bug-cascade` | 修日期解析 bug → 依赖旧行为的模块崩溃 | 中 |
| `add-validation` | 加输入校验 → 边界数据不通过 | 中 |

每个场景都有：沙箱隔离、基线测试、Agent 执行、回归检测。

## 社区数据：提交 → 验证 → 回流

RRLabBench 不做「官方排行榜」。我们公开审计工具，社区各自跑自己的模型，数据回流后生成匿名化的效率对比报告。

### 数据怎么提交

```bash
# 1. 跑审计（保存结果）
rrlab-bench audit --model YOUR_MODEL --all-scenarios --runs 3 -o results.json

# 2. 一键提交
rrlab-bench submit --file results.json
# → 自动打开 GitHub Issue，标题和内容已预填好
# → 你只需点击「Submit new issue」
```

也可以直接指定模型和场景：
```bash
rrlab-bench submit --file results.json --model "deepseek-v4-pro" --scenarios refactor-api fix-bug-cascade
```

### 数据怎么回流

```
用户提交 (Issue/PR)
  → CI 自动验证 JSON 格式 + 必填字段
    → 去重检查（同模型同场景不覆盖已有数据）
      → 归档到 data/community/{模型}/{场景}.json
        → 每季度汇总生成社区报告
```

### 季度社区报告

每个季度从 `data/community/` 中提取所有经验证的数据，生成匿名化的效率对比：

```
2026 Q3 社区审计报告
  参与模型: 15
  新增数据: 42 条
  ┌──────────────┬───────┬──────┬────────┬───────┐
  │ 模型         │ 回合  │ 耗时 │ Token  │ 费用  │
  ├──────────────┼───────┼──────┼────────┼───────┤
  │ 用户提交 A   │ 8     │ 35s  │ 42K    │ ¥0.21 │
  │ 用户提交 B   │ 15    │ 98s  │ 110K   │ ¥1.45 │
  │ ...          │       │      │        │       │
  └──────────────┴───────┴──────┴────────┴───────┘
```

报告发布在 GitHub Releases，不排名、不评价——只做数据可视化。

### 提交规范

- 模型必须使用 **最高思考等级** 运行
- 数据包含 token 用量、耗时、费用
- 不要求 FRR > 0%（0% 也是有效数据）
- 可选的附加信息：模型版本、API 提供商、运行日期

## 参考数据

RR Lab 内部审计了 9 个模型配置，完整数据见 [`data/benchmarks/`](data/benchmarks/)。这不是排名，是参考基线。

<details>
<summary>展开查看参考数据</summary>

| 模型 | 回合 | 耗时 | Token | 费用/次 |
|------|:---:|:---:|:---:|:---:|
| Grok 4.5 | 6 | 23s | 19K | ¥0.31 |
| DS Flash | 14 | 39s | 71K | ¥0.07 |
| DS Pro | 12 | 49s | 53K | ¥0.17 |
| MiniMax M3 | 12 | 72s | 59K | ¥0.15 |
| GLM 5.2 | 10 | 84s | 34K | ¥0.30 |
| Opus 4.8 | 7 | 81s | 35K | ¥1.98 |
| Kimi K3 | 10 | 124s | 45K | ¥1.17 |
| Opus5-Medium | 12 | 77s | 73K | ¥3.19 |
| Opus5-MAX | 21 | 226s | 228K | ¥9.94 |

所有模型 FRR = 0%，差异仅在效率维度。
</details>

## 项目结构

```
rrlab-bench/
├── src/
│   ├── core/           # 沙箱、Agent 循环、测试运行器、工具执行
│   ├── scenarios/      # 三场景定义（refactor_api, fix_bug_cascade, add_validation）
│   └── evaluators/     # FRR 评分器、测试完整性检查
├── scripts/
│   └── run_bench.py    # 批量运行脚本
├── data/
│   ├── benchmarks/     # RR Lab 参考数据
│   └── community/      # 社区贡献数据（待建设）
├── docs/               # 方法论白皮书
├── charts/             # 可视化图表
└── tests/              # 框架自身测试
```

## 许可

Apache 2.0 — 自由使用、修改、分发。审计数据属于提交者。
