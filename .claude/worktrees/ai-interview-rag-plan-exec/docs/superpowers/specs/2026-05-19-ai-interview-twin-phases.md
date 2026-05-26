# AI 面试分身阶段执行文档

## 1. 文档目的

本文档用于补充 [2026-05-19-ai-interview-twin-design.md](./2026-05-19-ai-interview-twin-design.md) 与 [2026-05-19-ai-interview-twin-plan.md](../plans/2026-05-19-ai-interview-twin-plan.md)，将当前项目的实施过程拆解为可逐阶段验收的执行节奏。

目标不是替代设计文档或实现计划，而是明确：

- 每个阶段要完成什么
- 每个阶段涉及哪些目录、文件与模块
- 每个阶段的输出结果是什么
- 每个阶段的验收标准是什么
- 每个阶段完成后必须暂停，等待用户确认后再进入下一阶段

该文档遵循当前项目的核心定位：

- 单页 AI 面试分身
- 支持文字 / 语音双模切换
- 回答围绕候选人的真实经历展开
- 通过 persona + RAG + layered memory 支撑长对话一致性
- 不做 MCP 集群与多 Agent 平台化扩展

---

## 2. 阶段划分原则

当前项目按三大阶段推进，每一阶段都必须具备可见成果，并且每一阶段都应能单独向用户展示结果。

这样划分的原因是：

1. 避免一次性并行推进前端、后端、语音链路，导致调试面过大
2. 优先把最容易直观看到的部分交付出来，便于尽早确认方向正确
3. 将“页面效果”“交互流程”“后端能力”拆开，分别验收
4. 保留随时调整范围的空间，避免前面设计很好、后面实现偏航

三个阶段分别是：

1. 第一阶段：目录结构与基础骨架
2. 第二阶段：前端页面与交互壳
3. 第三阶段：后端问答链路与联调

每个阶段完成后，Claude 必须停止继续实现，向用户展示阶段成果，等待用户明确确认后再进入下一阶段。

---

## 3. 第一阶段：目录结构与基础骨架

### 3.1 阶段目标

第一阶段的目标是：

- 把原本面向多页面个人中心的工程结构，收敛到 AI 面试分身单页方向
- 建立后续开发所依赖的目录、入口、占位文件与文档边界
- 让项目在结构层面清晰地反映当前产品定位
- 不追求真实功能，只确保骨架正确、职责边界明确

这是后续所有工作的地基。这个阶段做得清楚，后续前端和后端实现都会顺很多。

### 3.2 阶段范围

本阶段只处理以下内容：

#### 前端侧

- 将 `frontend/src/router/index.ts` 从多页面路由收敛为单页入口
- 保留 `frontend/src/App.vue` 作为根级 `RouterView` 容器
- 新建 `frontend/src/pages/interview/InterviewPage.vue` 作为唯一页面入口
- 暂不实现完整聊天 UI，只需提供可运行的基础页面占位

#### 后端侧

- 暂不实现真实 interview API
- 明确后端后续将新增的模块职责
- 保持现有 FastAPI 启动结构可用
- 为后续 `interview.py`、`persona.py`、`retrieval.py`、`memory.py` 等模块预留规划

#### 资料与语音边界侧

- 建立 `knowledge/` 目录，用于后续存放：
  - 简历资料
  - 项目资料
  - 技术笔记
  - 面试问答素材
- 建立 `services/voice/` 的边界说明或占位文档
- 明确语音项目与主后端的职责分工

#### 文档侧

- 更新 `README.md`，让项目描述与当前单页 AI 面试分身方向一致
- 保留已有设计文档与实现计划文档
- 新增本阶段执行文档，作为分阶段验收说明

### 3.3 建议涉及的目录与文件

本阶段建议创建、修改或确认以下文件：

#### 需要修改

- `README.md`
- `frontend/src/router/index.ts`
- `frontend/src/App.vue`（通常只需确认，不一定需要实质改动）

#### 需要创建

- `frontend/src/pages/interview/InterviewPage.vue`
- `knowledge/resume.md`
- `knowledge/projects.md`
- `knowledge/notes.md`
- `knowledge/interview_qa.md`
- `services/voice/README.md`
- `docs/superpowers/specs/2026-05-19-ai-interview-twin-phases.md`

### 3.4 具体实施内容

#### 3.4.1 路由收敛

目标是将当前类似 Dashboard / Projects / Notes / Status 的多入口结构，收敛为一个唯一首页：

- 路径：`/`
- 页面：`InterviewPage`
- 命名：`interview`

这样做的意义是：

- 产品定位统一
- 避免历史多页结构继续干扰后续开发
- 前端页面逻辑自然围绕单页展开

#### 3.4.2 单页入口占位

`InterviewPage.vue` 在本阶段不要求完成聊天体验，但至少应包含：

- 页面标题
- 简短说明文案
- 可体现 AI interview twin 定位的视觉占位
- 与现有 Tailwind / 视觉基调兼容的基础布局

目的不是炫技，而是让第二阶段的 UI 开发有一个稳定容器。

#### 3.4.3 资料目录建模

`knowledge/` 目录建议直接创建基础 md 文件，而不是只留空目录。

原因是：

- 后续 retrieval 和 persona 设计都依赖知识源的存在
- 即使第一版先写占位内容，也能提前固定数据组织方式
- 后续替换真实内容时风险更小

建议文件职责如下：

- `knowledge/resume.md`：候选人简历与背景
- `knowledge/projects.md`：项目经历与亮点
- `knowledge/notes.md`：技术笔记、技术反思
- `knowledge/interview_qa.md`：面试高频问答整理

#### 3.4.4 语音边界占位

`services/voice/README.md` 应说明：

- 该目录承接现有火山引擎实时语音项目
- 主后端负责问答逻辑，不负责音频传输
- 语音链路必须复用主会话 `session_id`
- 文字模式与语音模式不能分裂成两套上下文系统

这样在第三阶段接语音时，就不会再反复讨论边界。

### 3.5 本阶段不做的内容

第一阶段明确不做：

- 聊天消息流组件
- markdown 渲染
- 状态面板
- 文字/语音切换交互
- interview API
- persona / retrieval / memory 实现
- 真实 ASR / TTS 接入
- 前后端联调

也就是说，第一阶段的重点只有一个：**把结构搭对，把边界定清楚。**

### 3.6 阶段输出结果

第一阶段完成后，用户应该能看到：

1. 项目目录已经明显从“多页面个人中心”转向“单页 AI 面试分身”
2. 前端访问首页时，能看到单页入口的基础占位页面
3. `knowledge/` 目录已经建立，知识源结构清晰
4. `services/voice/` 的职责边界已经被写明
5. README 与当前产品定位一致

### 3.7 验收标准

用户验收第一阶段时，应重点检查：

- 路由是否已经收敛为单页
- 页面入口是否跑通
- 目录命名是否清晰
- 文档是否能准确表达当前产品方向
- 是否没有过早引入与当前阶段无关的复杂实现

### 3.8 阶段结束后的暂停规则

第一阶段完成后必须暂停，并向用户展示：

- 新的目录结构
- 首页占位效果
- 新增的知识源目录与语音边界文档

只有在用户确认“可以继续”后，才进入第二阶段。

---

## 4. 第二阶段：前端页面与交互壳

### 4.1 阶段目标

第二阶段的目标是：

- 完成单页聊天 UI 的主体结构
- 让用户可以直观看到最终产品的大致样子
- 在不依赖真实后端能力的前提下，把前端体验先做出来
- 固定页面布局、信息层次与交互方式

这一阶段的核心不是“回答是否智能”，而是“这个产品看起来是否像一个专业、可信的 AI 面试终端”。

### 4.2 阶段范围

本阶段聚焦前端页面与本地交互壳，不做真实后端问答链路。

#### 页面结构要完成

- 顶部标题区
- 模式切换区
- 消息流展示区
- 状态信息区
- 底部输入区
- 语音控制区

#### 交互壳要完成

- 文字 / 语音模式切换
- 消息列表渲染
- markdown 回答展示
- 来源标签展示能力
- 状态展示能力
- 新开一轮面试 / 清空会话入口

#### 数据来源方式

- 允许使用前端本地假数据或占位消息
- 允许临时模拟发送消息后的 UI 状态变化
- 暂不要求接真实 API

### 4.3 建议涉及的目录与文件

#### 需要创建

- `frontend/src/components/chat/InterviewHeader.vue`
- `frontend/src/components/chat/ModeSwitch.vue`
- `frontend/src/components/chat/MessageList.vue`
- `frontend/src/components/chat/MessageBubble.vue`
- `frontend/src/components/chat/ComposerBar.vue`
- `frontend/src/components/chat/StatusPanel.vue`
- `frontend/src/components/chat/VoiceControls.vue`
- `frontend/src/composables/useInterviewSession.ts`
- `frontend/src/composables/useVoiceMode.ts`
- `frontend/src/services/chat.ts`（可先保留接口壳）
- `frontend/src/types/interview.ts`

#### 需要修改

- `frontend/src/pages/interview/InterviewPage.vue`
- `frontend/package.json`（若加入 markdown 渲染与高亮依赖）

### 4.4 页面结构细节

#### 4.4.1 顶部区域

顶部应至少包含：

- 项目标题：AI Interview Twin 或等价表达
- 一句定位说明
- 模式切换按钮

它承担两个作用：

1. 告诉面试官这是什么产品
2. 第一眼建立“这是一个专用 AI 面试系统”的认知

#### 4.4.2 主消息区

主消息区应支持：

- 区分 interviewer / assistant
- 气泡或卡片式消息展示
- assistant 消息支持 Markdown
- assistant 消息可展示来源标签
- 消息排版适合较长回答阅读

因为这个页面不是普通 IM，对 assistant 回答的阅读体验要求更高。

#### 4.4.3 状态面板

状态面板建议展示：

- 当前系统状态：idle / listening / transcribing / retrieving / thinking / responding
- 当前面试主题
- 当前激活的资料来源标签

状态面板的价值不仅是 UI 补充，更是用来体现：

- 这个系统不是黑盒
- 它有明确的内部阶段
- 你理解 AI 系统的可解释性表达

#### 4.4.4 输入与控制区

输入区应支持：

- 文本输入
- 发送按钮
- 新一轮面试按钮
- 语音控制区
- 语音播报开关

文字与语音虽然模式不同，但都必须在同一个页面交互结构内完成，不能拆成两套界面。

### 4.5 状态与本地逻辑细节

本阶段即使还没有真实后端，也应提前固定状态模型，例如：

- `InterviewMode`
- `InterviewStatus`
- `InterviewMessage`
- `SourceTag`

这样做的原因是：

- 可以先把 UI 的契约固定住
- 第三阶段接后端时改动会更小
- 代码结构不会因为后端接入而大面积返工

### 4.6 本阶段不做的内容

第二阶段明确不做：

- 真实 interview API
- persona prompt 构建
- retrieval 检索逻辑
- memory summary
- selective memory write-back
- 真实语音接入

第二阶段的任务是：**把产品“长出来”，但还不把大脑接进去。**

### 4.7 阶段输出结果

第二阶段完成后，用户应该能看到：

1. 单页聊天界面已经基本成型
2. 页面风格符合“高级、专业、可信”的展示目标
3. 可以切换文字 / 语音模式
4. 可以看到消息流、状态面板、输入区、语音控制区
5. 即使后端还没接入，也能直观看到最终产品的大致体验

### 4.8 验收标准

用户验收第二阶段时，应重点检查：

- 页面整体视觉是否满意
- 信息层级是否清晰
- 消息展示是否舒服
- 模式切换是否自然
- 状态面板是否有存在价值
- 页面是否已经足够像一个完整产品，而不是半成品 demo

### 4.9 阶段结束后的暂停规则

第二阶段完成后必须暂停，并向用户展示：

- 页面整体效果
- 文字/语音模式切换效果
- 消息展示与状态区布局
- 当前交互壳是否符合预期

只有在用户确认页面方向没问题后，才进入第三阶段。

---

## 5. 第三阶段：后端问答链路与联调

### 5.1 阶段目标

第三阶段的目标是：

- 建立真实的 interview API
- 把 persona、retrieval、layered memory、write-back 串成统一回答链路
- 打通前后端文字问答流程
- 为后续接入现有火山语音项目提供稳定接口边界

这是整个项目的“智能中枢”阶段。

### 5.2 阶段范围

#### 后端 API

需要实现：

- 聊天请求模型
- 聊天响应模型
- `/api/interview/chat` 接口
- FastAPI 路由注册

#### 后端服务能力

需要实现：

- persona prompt 组装
- knowledge loader
- retrieval 检索
- recent turns buffer
- session summary memory
- selective memory write-back 判定与沉淀
- answer pipeline 串联

#### 前后端联调

需要实现：

- 前端发送文字问题到后端
- 后端返回回答与来源标签
- 前端更新消息流与状态面板
- 会话主题和 sources 正确展示

#### 语音边界对接准备

第三阶段不一定要完整接入真实火山语音链路，但至少要保证：

- 文字模式已经完全打通
- 语音模式未来只是在输入输出层接入
- 主问答链路不依赖具体语音实现

### 5.3 建议涉及的目录与文件

#### 需要创建

- `backend/app/api/interview.py`
- `backend/app/schemas/interview.py`
- `backend/app/services/persona.py`
- `backend/app/services/retrieval.py`
- `backend/app/services/memory.py`
- `backend/app/services/memory_summary.py`
- `backend/app/services/memory_writeback.py`
- `backend/app/services/knowledge_loader.py`
- `backend/app/services/answer_pipeline.py`
- `backend/tests/test_interview_api.py`
- `backend/tests/test_persona.py`
- `backend/tests/test_retrieval.py`
- `backend/tests/test_memory_layers.py`

#### 需要修改

- `backend/app/api/__init__.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `frontend/src/services/chat.ts`
- `frontend/src/composables/useInterviewSession.ts`
- `frontend/src/types/interview.ts`
- `frontend/src/pages/interview/InterviewPage.vue`

### 5.4 后端链路细节

#### 5.4.1 Persona

Persona 层至少要明确：

- 系统始终以候选人身份回答
- 优先引用真实资料
- 允许围绕真实经历解释技术原理
- 明确禁止编造经历、职责、结果

这不是一个装饰性 prompt，而是回答可信度的第一层约束。

#### 5.4.2 Retrieval

Retrieval 第一版不要求复杂向量库，也可以先用轻量规则或本地文本匹配完成可演示版本。

但必须体现：

- 检索是基于候选人资料的
- 返回结果能被回答链路消费
- 前端最终能看到 sources

#### 5.4.3 Layered Memory

记忆层至少应实现三部分：

1. `Recent Turns Buffer`
   - 保存最近几轮原始对话
   - 服务当前连续追问

2. `Session Summary Memory`
   - 将当前对话提炼成压缩摘要
   - 减少上下文无限增长的问题

3. `Selective Memory Write-back`
   - 识别高价值回答
   - 选择性沉淀为可复用知识

这部分是项目的技术亮点之一，不能只做名字，不做行为。

#### 5.4.4 Answer Pipeline

回答链路建议固定为：

输入问题 → recent turns → session summary → retrieval → persona 组装 → 回答生成 → memory 更新 → 返回前端

这样可以保持：

- 顺序清晰
- 可解释性强
- 后续便于替换具体 LLM 实现

### 5.5 测试与验证细节

第三阶段必须补足测试与验证，不然这个项目很容易只剩页面好看。

建议至少覆盖：

- API 是否可正常返回 reply 与 topic
- persona 是否包含“不编造经历”的约束
- retrieval 是否能返回匹配资料
- recent turns 是否能按上限裁剪
- summary 是否能正确反映当前主题
- write-back 是否能筛选高价值回答
- 前端是否能接到后端响应并更新 UI

### 5.6 本阶段输出结果

第三阶段完成后，用户应该能看到：

1. 页面已经不是静态壳，而是能真实问答
2. 回答围绕候选人真实资料展开
3. 状态面板与 source tags 能反映后端处理结果
4. 系统已经有 layered memory 的基础能力
5. 项目具备可以继续接入火山语音实时链路的清晰边界

### 5.7 验收标准

用户验收第三阶段时，应重点检查：

- 文字模式问答是否可用
- 回答是否真的基于候选人资料
- 长对话是否还能保持上下文
- memory summary 是否有实际意义
- selective write-back 是否不是空口概念
- 页面和后端联动是否稳定

### 5.8 阶段结束后的暂停规则

第三阶段完成后也必须暂停，向用户展示：

- 可运行的文字问答流程
- retrieval 命中效果
- memory 分层效果
- 前后端联调结果

在这一阶段之后，才进入额外优化，例如：

- 真实火山 ASR/TTS 完整接入
- 流式输出优化
- 资料组织进一步细化
- demo 文案与面试话术打磨

---

## 6. 每阶段统一验收规则

每个阶段都必须遵守以下规则：

1. 完成当前阶段目标后，立即暂停，不得自动进入下一阶段
2. 向用户展示当前阶段的可见成果，而不是只说“做完了”
3. 明确说明：
   - 改了哪些文件
   - 当前可以看到什么效果
   - 下一阶段准备做什么
4. 等待用户确认后，再继续下一阶段

建议阶段结束时统一采用类似表达：

> 当前阶段已完成，我已经把可见结果准备好。你先验收这一阶段；如果你确认没问题，我再继续下一阶段。

---

## 7. 当前执行建议

基于本项目当前状态，推荐执行顺序如下：

1. 先执行第一阶段：目录结构与基础骨架
2. 通过后执行第二阶段：前端页面与交互壳
3. 再执行第三阶段：后端问答链路与联调

这样做的最大好处是：

- 你可以很早看到可见成果
- UI 方向可以提前修正
- 后端不会在错误的页面结构上白做
- AI 能力的复杂度被放在最后处理，更稳

---

## 8. 结论

这个项目最适合采用“阶段式收敛”的方式推进，而不是一次性把所有模块一起做完。

最终节奏应当是：

- 第一阶段定结构
- 第二阶段看页面
- 第三阶段接大脑
- 每阶段结束都暂停，等待用户验收

这不仅能降低实现风险，也更符合你当前“面试展示项目”的目标：
**优先把可见效果做对，再把智能能力接稳。**
