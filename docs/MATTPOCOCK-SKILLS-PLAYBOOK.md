# Matt Pocock Engineering Skills Playbook (`mattpocock/skills`)

> 沉淀来源：`mattpocock/skills`（已裁剪并安装至 `~/.agents/skills/`，同步注册于 `~/.gemini/config/skills.json`）

## 1. 核心设计哲学：双轴分层（User-Invoked vs Model-Invoked）

Matt Pocock 将工程 Skill 按**谁触发**拆成严格正交的两层：
1. **User-Invoked（用户主动触发的编排器）**：只在用户敲指令时运行，负责串起整个工程流程（如 `/grill-with-docs`、`/to-spec`、`/to-tickets`、`/implement-spec`、`/improve-codebase-architecture`、`/retro`、`/chief-of-staff`、`/software-factory`）。**铁律：用户触发型 Skill 绝不互相调用，但可以调度下层的模型纪律型 Skill。**
2. **Model-Invoked（模型自动遵循的工程纪律）**：可由用户触发，也可被编排器或 Agent 在合适时机自动拉起，固化底层内功：
   - `codebase-design`（Ousterhout **深模块 Deep Modules** + Feathers **接缝 Seam**）
   - `domain-modeling`（DDD 统一语言 `GLOSSARY.md` + 慎用 ADR）
   - `tdd`（垂直切片 **Tracer Bullets** + 在确认过的 Seam 做红-绿循环，严禁先写完所有测试的水平切片）
   - `diagnosing-bugs`（**无红灯闭环，不准读代码猜原因**：必须先造一个 `<2s` 必现红灯命令，再二分/假设/修补）
   - `code-review`（**双轴并行独立审查**：Standards 轴对照规范与 12 种 Fowler 代码坏味道；Spec 轴对照原始需求与防 Scope Creep，两路 subagent 互相隔离防止互相污染）
   - `writing-for-agents`（区分 Context Load 与 Cognitive Load，用 **Leading Words** 锚定模型先验，用正向指令替代 `"不要做X"` 的大象悖论，删掉所有 no-op 废话）

---

## 2. 解决 AI 编程四大典型翻车模式的最佳实践表

| 翻车模式 | 根因 | 对治 Skill | 操作要点 |
|---|---|---|---|
| **1. 写出来不是我要的** | 需求模糊时直接让 AI 写代码 | `grill-with-docs` / 内置 `/grill-me` | 沿决策树逐分支拷问直到全清晰；顺手把新术语写进根目录 `GLOSSARY.md`（不写实现细节），省后续大量思考 Token。 |
| **2. 代码一跑就碎 / 假绿** | 缺乏可信反馈闭环或只测 mock | `tdd` + `diagnosing-bugs` | ① `tdd` 每次只切一个**垂直 Tracer Bullet**（UI→API→DB→测试全打通一点）；② 排错先建**红灯复现指令**，再去猜 3–5 个假设。 |
| **3. 越改越烂成泥球** | AI 喜欢把小函数拆成浅封装 | `codebase-design` + `improve-codebase-architecture` | 记住口诀：**接口越窄、实现越厚越好（Deep Module）**；用**删除测试**判断浅模块；定期跑架构扫描出 HTML 报告挑痛点深化。 |
| **4. 多步/多 Agent 失忆与漂移** | 单窗口膨胀 + 缺持久状态机 | `to-spec` → `to-tickets` → `implement-spec` → `chief-of-staff` | 用任务依赖图（Task Graph + `Blocked by`）按 Frontier 并发派工；每条 `implementer` 在独立 worktree + 新鲜上下文窗口执行；收工用 dated Wiki 沉淀事实并附 commit/日期。 |

---

## 3. 与当前工作流（Antigravity + T3 Code + Fleet-Hub）的结合姿势

1. **做新功能前**：在 Antigravity 或 T3 Code 先跑 `/grill-with-docs`（或 `/grill-me`），把领域名词沉淀进项目 `GLOSSARY.md`，再让 `/to-spec` → `/to-tickets` 切出可并发的 Tracer-Bullet 切片。
2. **修疑难 Bug 时**：明确调用 `diagnosing-bugs`——先让 Agent 交出一个已跑红的 2 秒复现命令，再看代码提 3–5 个假设。
3. **跨 Agent 接力 & 上下文瘦身**：会话超 100k tokens 时运行 `/handoff`（写入 `$TMPDIR` 脱敏交接文档 + 推荐下一程 Skill），或切到 **T3 Code (`http://127.0.0.1:3773`)** 开新 Worktree 线程并发跑。
4. **周度架构体检**：用 `improve-codebase-architecture` 扫描最近 git 热点文件，把拆太碎的浅模块合并成深模块。
5. **自动化防翻车三闸（`software-factory`）**：**自动检查（typecheck/test）→ 独立双轴 `code-review` → 人工黄区拍板**。
