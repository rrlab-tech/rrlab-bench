# Bench-Harness v0.1 — 方向存档

> **项目定位**：RRLabBench 的中长期延伸方向。从"测模型"扩展到"测/进化 Harness"。
> **状态**：方向已论证，未动工。本文档用于存档动机、问题定义和最小路径，防止后续迷失方向。
> **创建**：2026-07-28
> **触发**：Lilian Weng《Harness Engineering for Self-Improvement》(2026-07-04) + 内部讨论

---

## 1. 背景与动机

### 1.1 外部触发

Lilian Weng 2026-07 博文系统梳理了 Harness Engineering 领域：
- **Harness = 模型外围的运行时系统**（工作流、评估、权限、持久状态管理），类比 OS
- 核心趋势：harness 本身成为优化对象，用代码定义、用进化算法搜索
- 代表工作：Meta-Harness、Self-Harness、AHE、Darwin Gödel Machine、ADAS、AFlow

关键发现（与本项目直接相关）：
- **Harness 改进能力与模型大小无关**（9B 到 Opus 扁平）——呼应我们 benchmark 结论"大模型在 agent 场景不一定更好"
- **代码是 harness 的通用语言**——markdown 规则是进化瓶颈
- **AHE 的可观测性三支柱**：组件可观测、经验可观测、决策可观测——每次 harness 编辑必须有失败证据支撑且可证伪

### 1.2 内部动因

Pi Agent 已有一组 harness 组件在运行：
- AGENTS.md（规则层，pi-reflect 每天自动优化）
- 多模型 escalation 系统
- early compaction 配置
- pi-self-learning / pk-pi-hermes-evolve

**现状问题**：这些改动**没有任何验证机制**。pi-reflect 改了规则，无法回答"改好了还是改坏了"。目前处于 ACE→MCE 过渡阶段：有自动优化，但搜索空间局限于 markdown 文本，且缺少反馈回路。

---

## 2. 问题定义：为什么不能直接用 RRLabBench 做验证层

经讨论论证，RRLabBench 当前形态**不能**直接作为 harness 进化的验证层，存在一个结构性问题：

### 2.1 核心问题：Harness 错位（致命）

RRLabBench 的 `agent_loop.py` 有**自己的 harness**（硬编码 system prompt + 工具集 + 执行循环）。测的是"模型在 RRLabBench harness 下的表现"。

Pi 的 AGENTS.md 改动改的是 **Pi 的 harness**。两者之间**无传导机制**——改 AGENTS.md，RRLabBench 分数不会有任何变化。

> 类比：用汽车碰撞测试验证飞机座椅改进——测试环境不是被测对象运行的环境。

### 2.2 次要问题

| 问题 | 说明 |
|------|------|
| 粒度太粗 | 场景是集成测试，一个场景混合考察多维度，单点 harness 改动被噪声淹没 |
| 统计功效不足 | 每场景 1 次运行，5% 提升无法与模型方差区分 |
| Goodhart 风险 | 场景池小且固定，harness 进化会过拟合这 10 个场景 |
| 覆盖偏差 | compaction 策略、escalation 决策等 harness 组件无法被现有场景触达 |

### 2.3 RRLabBench 的正确定位

按 AHE 框架，RRLabBench 适合作为 **held-out 回归测试**——验证 harness 改动"没把别的搞坏"，而非验证"改动有效"。必要但不充分。

---

## 3. v0.1 设计

### 3.1 目标

建立 Pi harness 进化的最小验证闭环：

```
pi-reflect 提出 AGENTS.md 改动
   ↓
定向探针（probes/）验证"改动有效"
   ↓
RRLabBench 全量回归验证"没搞坏别的"
   ↓
合并 / 回滚
```

### 3.2 三个改造点（按优先级）

**① Harness 可注入（前提，~20 行改动）**

把 RRLabBench `agent_loop.py` 的硬编码 system prompt 改为从外部文件加载。这样 AGENTS.md 可直接灌入测试，解决错位问题。

**② 定向探针 probes/**

从 pi-reflect 历史失败记录中挑典型案例，写成微型场景：

- 每条 AGENTS.md 规则 ↔ 一组探针
- 判定确定性：用文件系统状态/工具调用序列直接断言，**不用 LLM judge**（消除评估噪声）
- 改动某条规则只需跑对应探针 + 全量回归

示例：
```
规则："修改前先 read 确认当前状态"
探针：5 个微型场景（文件已过期/并发修改/不存在）
断言：agent 工具调用序列中 edit 之前必须有 read
```

**③ 探针来源：真实失败日志**

pi-reflect 每天回顾的对话里有现成失败模式，最小化复现成探针——生态效度最高，避免人造场景与真实使用脱节。

### 3.3 非目标（v0.1 明确不做）

- ❌ 自动化 harness 搜索（那是 Meta-Harness/DGM 层面，v0.2+ 再议）
- ❌ 代码化 harness（AGENTS.md 仍是 markdown，代码化是更大改造）
- ❌ 统计显著性框架（先跑通闭环，功效分析后置）
- ❌ 多 harness 对比（先支持"当前 AGENTS.md vs 候选 AGENTS.md"两两比较）

---

## 4. 长期演进方向（存档备查）

| 阶段 | 对应学术工作 | 能力 |
|------|------------|------|
| v0.1 | AHE 简化版 | 人工触发 harness 改动 + 探针验证 + 回归 |
| v0.2 | Self-Harness | 失败模式自动聚类 → 自动提出候选改动 |
| v0.3 | MCE | skill 级进化，规则库带版本谱系 |
| v0.4+ | Meta-Harness/DGM | harness 代码本身进入搜索空间 |

关键风险备忘（来自 Weng 文末挑战清单，与本项目强相关）：
- **Reward hacking**：评估器必须坐在进化循环之外（探针断言确定性、RRLabBench 只读）
- **多样性坍缩**：探针库要持续从真实失败补充，不能只在固定池里进化
- **负面结果**：失败的 harness 改动也要存档，避免重复踩坑

---

## 5. 当前状态与下一步

- [x] 方向论证完成（本文档）
- [x] 代码改造①：agent_loop harness 可注入（`run_agent_loop(harness_text=...)` + CLI `--harness` 参数，audit/run 均支持）
- [x] 代码改造②：probes/ 框架（`src/probes/runner.py` 确定性断言执行器 + `rrlab-bench probe` 子命令）
- [x] 首批 4 个探针（read-before-edit / no-blind-retry / verify-after-write / write-only-policy），端到端跑通
- [x] **完整闭环验证（2026-07-28）**：实验规则"禁用 edit_file 只用 write_file"，DS V4 Pro baseline FAIL（用了 edit_file）→ 注入 harness 后 PASS（切换到 write_file），同任务同模型，证明注入机制有效且探针可检测
- [x] 探针设计教训：task_complete 断言与规则无关，易造成假 FAIL，已从探针中移除（断言只针对规则本身）
- [x] 探针现状认知：前 3 个探针对 DS V4 Pro 无区分度（baseline 即遵守）——**探针必须从真实失败日志提取才有价值**
- [ ] 从 pi-reflect 日志提取真实失败模式，补充有区分度的探针
- [ ] 探针结果存档机制（harness 版本 × 探针分数的时间序列）
- [x] 提醒系统（2026-07-30）：手动检测的节奏提醒，不做自动执行
  - `com.rrlab.probe-weekly`：每周一 9:00 通知跑探针
  - `com.rrlab.probe-monthly`：每月 1 日 9:30 通知做探针影响分析（区分度/假阳性/覆盖漂移）
  - 脚本：`~/.rrlab/probe-remind.sh`，日志：`~/.rrlab/probe-reminders.log`
- [x] CLI 修复：`_resolve_model_config` 增加 GLM 官方路由（glm/zhipu → open.bigmodel.cn + ZHIPU_API_KEY），不再错误地走 DeepSeek/OpenRouter
- [x] 探针区分度实测（prefer-edit-over-write，16 行文件）：DS V4 Pro 和 GLM 5.2 baseline 均 PASS——简单场景对强模型无区分度，探针价值在于回归保护；区分度预期出现在大文件（百行级）或更弱模型上

**用法备忘**：
```bash
# 探针：baseline vs 注入 AGENTS.md 对比
python3 -m src.cli probe --model deepseek-v4-pro                        # baseline
python3 -m src.cli probe --model deepseek-v4-pro --harness /path/to/AGENTS.md

# 场景回归：带 harness 跑全量场景
python3 -m src.cli audit --all-scenarios --runs 3 --harness /path/to/AGENTS.md
```

**复盘点**：下次回到这个项目时，先读本文件第 3.2 节确认三个改造点哪些已完成。

---

## 6. 手动闭环期（v0.1 → v0.2 过渡，始于 2026-07-30）

### 6.1 pi-reflect 长会话失明 bug 修复（数据管道前提）

- **根因**：pi-reflect 按会话文件名日期过滤，而文件名日期 = 会话**启动**日。用户习惯多工作台并行 + Pi 进程永不关闭（单进程可运行 9 天+），新消息全部写入旧日期文件 → 7-28/29/30 连续三天扫描为 0，反思失明
- **修复**（`~/.pi/agent/git/github.com/jo-inc/pi-reflect/extensions/reflect.ts`，本地补丁）：① mtime 兜底识别活跃长会话 ② 长会话内按逐条 timestamp 过滤到目标窗口 ③ 完全无时间戳的文件排除（防误纳）
- **验证**：pi-reflect 全部测试通过；采集 dry-run 从 0 → 6 scanned / 5 included，两个长会话均可见
- **注意**：上游更新会覆盖补丁，值得提 PR（对所有重度用户普遍存在）
- **设计确认**：pi-reflect 就是定时调度（cron/launchd），无"关闭时触发"机制；每天一次频率合适（有自我节制：无实质会话跳过、当天已反思跳过）
- **2026-07-31 发现新问题**：修复后扫描成功（6 scanned / 5 substantive, 449KB），但 LLM 响应被截断——449KB ≈ 120K tokens，接近 DeepSeek 128K 上下文上限，JSON 解析失败。已修复：`reflect.json` maxSessionBytes 614400 → 200000（≈67K tokens），为输出留足空间

### 6.2 手动闭环 SOP（每次 AGENTS.md 变更后执行）

```bash
# 1. 确认 pi-reflect 是否改了 AGENTS.md（每天 04:00 运行）
tail -5 /tmp/pi-reflect.log

# 2. 若改了 → 先 diff 检查文本质量（2026-07-31 实战证明必要：merge 编辑会吞句/造重复行）
diff ~/.pi/agent/reflect-backups/$(ls -t ~/.pi/agent/reflect-backups/ | head -1) ~/.pi/agent/AGENTS.md
#    重点看：规则是否被误删、残句、重复行、格式破坏（缺列表前缀）

# 3. 文本没问题 → 跑探针验证行为
cd /Volumes/Other/Agent/rrlab/rrlab-bench
set -a && source /Volumes/Other/Agent/rrlab/config/credentials.env && set +a
python3 -m src.cli probe --model deepseek-v4-pro --harness ~/.pi/agent/AGENTS.md -o /tmp/probe_$(date +%m%d).json

# 4. 记录当日实验数据（时间序列，v0.2 决策依据）
python3 scripts/harness_log.py --probe-file /tmp/probe_$(date +%m%d).json \
    --bad-edits <N> --note "<当日要点>"
```

**数据文件**：`data/harness-log/harness-log.jsonl`（JSONL，一天一行，含 reflect 编辑数/坏编辑数 + 探针通过率）

首次执行：2026-07-31 早上（04:00 的 reflect 是修复后首次真实运行）。

**2026-07-31 首次实战事件（负面结果存档）**：
- 04:00 运行：扫描成功（修复生效）但 LLM 输出截断，无编辑。修复 maxSessionBytes 614400→200000
- 08:33 运行：成功应用 6 条编辑，其中 **2 条有害**：误删"自动化优先"规则、"渐进式优化"被截断成残句（merge 操作时吞掉前半句）。手动 diff 发现后恢复
- **教训**：merge 类编辑是 LLM 常见失败点（吞前半句）；没有 diff 检查，坏编辑会静默生效。这正是验证层存在的意义——6.2 SOP 中的 diff 检查不是可选项

### 6.3 v0.2 进入条件（不要提前自动化）

v0.2 的本质已明确：**把手动闭环自动化**（diff 检测 → 自动跑探针 → 结果回写 reflect 输入，如"你上次加的规则让探针 X 挂了"）。不是新能力。

手动跑 2-4 周，两个确认标准都满足才进入 v0.2：
1. 探针无假阳性骚扰（FAIL 都是真问题）
2. pi-reflect 的规则改动能被探针区分出好坏

若探针总误报或测不出差异 → 先修探针库，v0.2 推迟。

### 6.3.1 v0.2 备选路径：自研 reflect 组件（2026-07-31 决策框架）

**背景**：pi-reflect 一周实战暴露 5 类问题，其中 3 类在核心编辑链路（merge 吞句、重复已有内容、破坏格式），坏编辑率 33%（6 条中 2 条）。补丁修不了核心质量问题。

**量化触发条件**：手动期内若 pi-reflect 坏编辑率 > 20%（每 5 次编辑 1 次有害）→ 启动自研。

**自研范围（约 200-300 行，基于已有基础设施）**：
1. 会话扫描：复用已修复的 mtime+timestamp 逻辑
2. DS V4 Pro 分析 prompt：**全量输出新 AGENTS.md，禁用 merge 编辑**（AGENTS.md 仅 3KB，merge 是为大文件设计的过度工程，也是 3/4/5 号问题根源）
3. diff 预览 + 探针验证 + 人工确认后写入
4. 与探针结果联动的反馈回路（v0.2 核心，pi-reflect 不会为我们加）

**若手动期 pi-reflect 表现改善，则维持现状不重写——数据替我们做决定。**

### 6.4 待办汇总（当前优先级排序）

1. **每日**：reflect 后若 AGENTS.md 变更，按 6.2 SOP 手动跑探针
2. **从 pi-reflect 日志提取真实失败模式**，补充有区分度的探针（现有探针对强模型区分度低）
3. **给 pi-reflect 上游提 PR**（长会话修复）
4. 探针结果存档机制（harness 版本 × 探针分数时间序列）
5. GLM 5.2 官方直连重跑（见 roadmap.md Phase 0）
