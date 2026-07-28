# RRLabBench — 社交媒体文案

## LinkedIn

We tested 9 LLMs on the same real-world coding task. All of them completed it correctly. Zero quality difference.

But here's the part that surprised us: the most expensive model cost ¥9.94 per task, while the cheapest did it for ¥0.07 — same result, 142x difference.

Even within similar quality tiers, the gaps were wild. Opus 5 at MAX thinking level spent 21 turns and 226 seconds over-verifying a task it had already solved. Dropping it to MEDIUM cut costs by 70% with identical output. Grok 4.5 finished the same task in 6 turns and 23 seconds.

So I built RRLabBench — an open-source audit tool that measures what existing benchmarks don't: efficiency. Turns taken, time spent, tokens burned, real cost. Not "how smart is this model" but "what will this model actually cost you at the end of the month."

It's not a leaderboard. You run it against your own tasks, on your own models, and decide for yourself. Community-submitted data gets anonymized into quarterly efficiency reports.

GitHub: https://github.com/rrlab-tech/rrlab-bench
First batch audit data: 9 models × 3 scenarios, all FRR=0%.

Happy to connect with anyone working on LLM evaluation, Agent reliability, or model selection for production.

---

## Reddit

**Title: We benchmarked 9 LLMs on the same coding task — all produced identical quality, but cost differed by 32x**

I've been frustrated by how disconnected benchmark scores feel from real usage. A model tops the leaderboard, then you actually use it in an Agent loop and it's slow, expensive, or both.

So I built a small audit tool called RRLabBench. It gives models the same real-world coding task (modify an API, fix a cascading bug, add input validation), runs them in a sandbox, and measures:

- Did they break anything? (regression risk)
- How many turns did they take?
- How long? How many tokens? What did it cost?

First batch: 9 models, 3 scenarios each. All models passed (FRR=0%). No quality difference whatsoever. But:

| Model | Turns | Time | Cost |
|-------|:-----:|:----:|:----:|
| Grok 4.5 | 6 | 23s | ¥0.31 |
| DeepSeek Flash | 14 | 39s | ¥0.07 |
| Opus 5 MAX | 21 | 226s | ¥9.94 |

32x cost difference for identical output. Opus 5 MAX spent most of those 21 turns re-verifying work it had already done correctly. Deep thinking = negative ROI in Agent scenarios.

The tool is open source: https://github.com/rrlab-tech/rrlab-bench

You can run your own models, and if you submit results back, they get included in quarterly anonymized community reports. No rankings, no "best model" — just data to help you pick what works for your use case.

Would love feedback from anyone who's been wrestling with model selection for production Agent workflows.

---

## Facebook

刚做完一个小实验，结果让我挺意外的。

我让 9 个大模型完成同一个编程任务：改 API、修 bug、加校验。真实场景，不是选择题。9 个模型全部做对了，质量上没有差别。

但成本差了 32 倍。

最快的 Grok 4.5 用了 6 轮、23 秒，花 ¥0.31。最贵的 Opus 5 MAX 用了 21 轮、226 秒，花 ¥9.94。任务完全一样，结果完全一样。

Opus 5 多的那十几轮去哪了？全耗在"反复检查自己已经做对的事"上。考试的时候深度思考是加分项，实际干活的时候，每一轮多出来的验证，都是你的时间和钱。

因为这次测试，我从公司离职专心做了这个开源项目——RRLabBench。它不搞排行榜、不评"谁最聪明"，只看一个实际的问题：完成同样质量的任务，哪个模型更快、更省、更便宜。

代码开源在 GitHub：https://github.com/rrlab-tech/rrlab-bench
跑一次就几行命令，结果自己看。也接受社区提交数据，每季度汇总匿名化的效率报告。

想把这件事推荐给所有在选模型、做 Agent 的朋友。排行榜上高几分不重要，月底账单才重要。
