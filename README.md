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

8 cases per language: 4 escalation cases (perf, churn, QBR, crash), 2 negatives, 1 approval-gate case and 1 rewrite-only case. Model: GLM-5.1 via miniagent, 1 run per configuration. Full details, per-case scores and known issues are in [`benchmarks/REPORT.md`](benchmarks/REPORT.md).

每种语言 8 个用例，模型为 GLM-5.1（通过 miniagent 运行），每种配置跑 1 次。完整报告、逐例得分和已知问题见 [`benchmarks/REPORT.md`](benchmarks/REPORT.md)。

| v1.0.1 | With skill | Baseline (no skill) |
|---|---|---|
| EN pass rate | **80.0%** (42 / 54 assertions) | 65.0% (34 / 54) |
| ZH pass rate | **93.1%** (50 / 54 assertions) | 70.6% (36 / 54) |
| Trigger accuracy | EN 19/20 · ZH 19/20 (recall 10/10 each) | |

Known weak spots: the QBR altitude ladder and backtest (case 3), stating the ambitious target up front in EN (case 1), and one false trigger on a "personal career goals" query.

已知不足：QBR 用例的高度阶梯和回测（用例 3）、英文版未先明确野心目标（用例 1），以及"个人职业目标"类请求会误触发一次。

## Credits / 致谢

The ideas come from **Felix Rieseberg**'s essay [How to be more ambitious: A tutorial for humans with models](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/). The Chinese translation is on WeChat (QbitAI / 量子位): [「大家用AI都太保守了！」Claude Code负责人：我的方法更有野心](https://mp.weixin.qq.com/s/DSkimaN8KLtSRI0UFNFaPA). The wording here is original apart from short marked quotations. This skill adds the fit check, approval gates, setup step, external verification and gap report. See [`references/sources.md`](references/sources.md).

思路来自 Felix Rieseberg 的文章《How to be more ambitious: A tutorial for humans with models》及量子位的中文译文。除少量标注的引用外均为原创表述，详见 [`references/sources.md`](references/sources.md)。

## License

MIT — see [LICENSE](LICENSE).
