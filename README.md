# ambition-loop

An agent skill that makes the model **raise the task, then actually deliver the harder version and prove it with an outside judge**. It finds the goal behind the goal (altitude), works from raw material using the field's best instruments (depth), and borrows methods from other fields (range). It then sets a hard, measurable target, executes, verifies, and ends with a gap report: asked vs ambitious vs achieved. Approval gates for cost, permissions, destructive actions and external actions stop it before anything risky, and if you say no, it stops.

一个 Agent 技能：先把任务**拔高**，再**真正把更难的版本做出来，并用外部裁判证明**。它会找到目标背后的目标（高度），从原始材料出发、用领域顶尖从业者的工具去做（深度），并借用其他领域的方法（广度）；然后定一个可度量、听起来不可能的目标，执行、验证，最后交一份差距报告，对比原始要求、野心目标和实际达成。花钱、权限、破坏性操作、对外操作都有审批闸门，被拒绝就停下。

Chinese version / 中文版：[`ambition-loop-zh/`](ambition-loop-zh/)（中文优先，与英文版步骤、闸门、评测一一对应）

## Workflow / 流程

| Step | What happens |
|---|---|
| 0 Fit check | Decide ESCALATE or AS-ASKED. Trivial asks, hotfixes and explicitly minimal requests are done as asked |
| 1–4 Survey · Altitude · Depth · Range | Look at reality, find the goal behind the goal, rewrite the task deeper rather than bigger, borrow methods |
| 5 Target | A specific, impossible-sounding, measurable target; the literal ask stays as the floor |
| 6 Approval gate | Plan card; G1 cost · G2 permissions · G3 destructive · G4 external/visible · G5 scope. Denied means stop |
| 7 Setup | Data, instruments, judge and baseline before the main work |
| 8 Execute | At least two distinct approaches; never quietly lower the target |
| 9 Verify | An outside judge for each claim (tests, benchmarks, held-out data, reproduction), never self-grading |
| 10 Gap report | Target comparison, verification, gaps, next moves, gated/skipped items; checked by `scripts/check_report.py` |

A rewrite-only mode (steps 0–6) hands over an improved prompt or plan without executing it.

只改写模式（第 0–6 步）只交出拔高后的提示词或计划，不执行。

## Install / 安装

```bash
npx skills add linkxzhou/ambition-loop
```

Chinese version / 安装中文版：

```bash
npx skills add linkxzhou/ambition-loop --full-depth --skill ambition-loop-zh
```

Or clone it into your skills folder / 或直接克隆：

```bash
git clone --depth 1 https://github.com/linkxzhou/ambition-loop.git ~/.claude/skills/ambition-loop
# Chinese only / 只要中文版：
cp -r ~/.claude/skills/ambition-loop/ambition-loop-zh ~/.claude/skills/ambition-loop-zh
```

## Structure / 结构

```
SKILL.md            # English skill: fit check, 11 numbered steps (Action / Output / Done when), gates, report format
references/         # Moves, judge ladder, article examples, self-efficacy, report template, sources
scripts/            # check_report.py: validates the final gap report
evals/              # 8 eval cases, 20 trigger queries and fixtures
ambition-loop-zh/   # 简体中文版，结构与英文版相同
benchmarks/         # Eval report, aggregated results, harness scripts, EN/ZH sync check
```

## Evals / 评测

8 cases per language: 4 escalation cases (perf, churn, QBR, crash), 2 negatives, 1 approval-gate case and 1 rewrite-only case.
- **Agent model (v1.0.2):** `glm-5.3-flash-external` via miniagent. Cases 1, 3 and 7 ran twice per arm, the rest once.
- **Judge:** a separate read-only LLM judge plus scripted checks.
- **Details:** full report, per-case scores and known issues in [`benchmarks/REPORT-v1.0.2.md`](benchmarks/REPORT-v1.0.2.md). The v1.0.1 report (GLM-5.1) is in [`benchmarks/REPORT.md`](benchmarks/REPORT.md).

每种语言 8 个用例。v1.0.2 的被测模型为 `glm-5.3-flash-external`（通过 miniagent 运行），用例 1、3、7 每种配置跑 2 次，其余跑 1 次。完整报告见 [`benchmarks/REPORT-v1.0.2.md`](benchmarks/REPORT-v1.0.2.md)。

| v1.0.2 (glm-5.3-flash-external) | With skill | Baseline (no skill) |
|---|---|---|
| EN pass rate | **89.9%** (70 / 78 assertions) | 68.3% (51 / 78) |
| ZH pass rate | **93.3%** (73 / 78 assertions) | 68.8% (52 / 78) |
| Trigger accuracy (2 samples) | EN 20/20 · 20/20 (recall 10/10, 0 false triggers) · ZH 18/20 · 20/20 (0 false triggers) | |

Pass rate is skill-creator's aggregate, weighting each run equally.

Compared with v1.0.1, the career-goals false trigger is gone (0 of 8 samples, previously 4 of 4). Case 1 (state the target up front, checked report) and case 7 (approval plan, no credential hunting) now pass every check in both runs.

Known weak spots:
- The QBR case still lacks an explicit 3-rung altitude ladder.
- One EN churn run did not load the skill; a rerun with the final description scored 8/8.
- "Go deeper on this analysis" is a borderline trigger.

已知不足：
- QBR 用例仍缺明确的三级高度阶梯。
- 英文流失分析用例有一次没有加载技能（用最终描述重跑得 8/8）。
- "go deeper on this analysis" 这类说法触发不稳定。

## Credits / 致谢

The ideas come from **Felix Rieseberg**'s essay [How to be more ambitious: A tutorial for humans with models](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/). The Chinese translation is on WeChat (QbitAI / 量子位): [「大家用AI都太保守了！」Claude Code负责人：我的方法更有野心](https://mp.weixin.qq.com/s/DSkimaN8KLtSRI0UFNFaPA). The wording here is original apart from short marked quotations. This skill adds the fit check, approval gates, setup step, external verification and gap report. See [`references/sources.md`](references/sources.md).

思路来自 Felix Rieseberg 的文章《How to be more ambitious: A tutorial for humans with models》及量子位的中文译文。除少量标注的引用外均为原创表述，详见 [`references/sources.md`](references/sources.md)。

## License

MIT — see [LICENSE](LICENSE).
