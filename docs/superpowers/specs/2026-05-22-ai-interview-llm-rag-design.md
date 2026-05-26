# AI 面试分身 LLM/RAG 接入设计

## 1. 目标

本次改造的目标是把旧智能客服项目中已经验证过的 LLM 与 RAG 能力接入到当前 AI 面试分身项目中，并让当前前端聊天页可以直接消费真实回答与引用来源。

本次按“最小可用版”推进，重点是尽快打通一条可运行、可联调、可展示的文字问答链路，而不是完整迁移旧项目的语音房间、RTC 场景和客服业务壳。

核心结果包括：

1. 当前后端新增真正可用的 interview chat API
2. API 内部完成“检索 -> 生成 -> 返回引用”的主链路
3. 当前前端聊天页改为调用真实后端，而不是停留在 mock
4. assistant 消息可以展示与回答绑定的 citations

---

## 2. 范围

### 2.1 本次包含

- 复用旧项目 LLM / RAG 的核心思路与配置模型
- 在当前 `backend` 中新增面向面试场景的服务层与 API
- 将旧项目的火山 Ark 模型调用能力接入当前项目
- 将旧项目的知识库检索能力接入当前项目
- 让检索结果同时服务于模型上下文与前端引用展示
- 让当前前端聊天页调用真实后端接口
- 让当前前端 assistant 消息渲染完整引用区
- 保持当前终端式面试页的 UI 主体不变，只做必要适配

### 2.2 本次不包含

- 迁移旧项目 RTC / StartVoiceChat / StopVoiceChat 相关链路
- 迁移旧项目场景配置 `SceneID` / `scenes` 体系
- 迁移旧项目语音房间前端页面
- 实现完整流式 SSE 返回
- 实现多知识库切换
- 实现 rerank、多路召回、复杂检索优化
- 实现知识库管理后台
- 实现长期 memory 平台

---

## 3. 现状与迁移依据

### 3.1 当前项目现状

当前项目后端仍是基础骨架：

- 配置入口在 `backend/src/app/core/config.py`
- API 目前只有 health 路由
- `interview_model` 仍为占位配置

前端面试页已经在往“消息下方展示 citations”的方向演进，且已存在 interview store、类型定义和聊天面板组件，因此最合理的接入方式不是迁移旧项目前端，而是把旧项目的能力接入当前前后端契约。

### 3.2 旧项目可复用能力

旧项目本地路径：`C:\Users\DXM-1002\Desktop\xuanyu\project_1\AI-language-speak`

本次确认可复用的核心能力有两块：

1. `server_final/services/llm_service.py`
   - 独立封装 Ark 模型调用
   - 基于环境变量初始化 client
   - 接收对话历史与 RAG 上下文后生成回答

2. `server_final/services/rag_service.py`
   - 独立封装知识库检索请求
   - 基于环境变量读取知识库配置
   - 通过 query 获取相关知识内容

旧项目中 `server_final/api/proxy.py` 的 `/api/chat_callback` 也证明了最小问答链路是成立的：

1. 读取用户消息
2. 先做 RAG 检索
3. 再调用 LLM 生成
4. 返回流式回答

### 3.3 不复用的旧项目部分

以下旧项目能力不应迁入本次最小版：

- `StartVoiceChat` / `StopVoiceChat`
- RTC token 生成
- `SceneID` / scene JSON 配置体系
- 语音房间 UI
- 与智能客服语境强绑定的 system prompt

原因是这些内容属于“语音客服产品壳”，不是当前 AI 面试分身最小版所需的核心能力。

---

## 4. 方案选择

本次考虑过三种接入方式：

### 方案 A：直接原样搬运旧服务层

直接把旧项目的 `llm_service.py`、`rag_service.py` 和路由逻辑复制到当前仓库，再做最小改名。

优点：

- 最快
- 风险低

缺点：

- 会把旧项目偏语音客服的语义带进来
- 路由契约和当前前端不自然匹配
- 旧 prompt 不适合面试场景

### 方案 B：复用能力，重写当前项目适配层（推荐）

保留旧项目中已验证过的“RAG 检索 + LLM 生成”能力，但在当前仓库里按现有后端结构和前端消息模型重新封装接口与数据结构。

优点：

- 最适合当前项目定位
- 前后端契约一次理顺
- 避免把旧项目无关负担迁入

缺点：

- 比直接搬运多一些适配工作

### 方案 C：先只接 LLM，不先接完整 RAG 引用

先打通模型回答，RAG 先置空。

优点：

- 实现最轻

缺点：

- 与当前项目正在推进的 citations 方向不一致
- 不能体现“基于真实资料回答”的产品价值

### 结论

采用方案 B：**复用旧项目能力，重写当前项目适配层。**

---

## 5. 总体架构

### 5.1 主链路

最小可用版的主链路如下：

1. 前端发送当前消息与最近对话历史到后端
2. 后端提取最后一条 interviewer 消息作为 query
3. 后端调用 `rag_service` 检索相关知识
4. `rag_service` 返回两份结果：
   - 给 LLM 的 `context_text`
   - 给前端的 `citations`
5. 后端调用 `llm_service`，把历史消息和 `context_text` 一起发给模型
6. 后端把模型输出包装成一条 assistant 消息
7. assistant 消息自带 citations 返回前端
8. 前端将该消息插入消息流，并在消息下方展示引用区

### 5.2 设计原则

#### 5.2.1 能力复用，契约重写

复用旧项目的已验证能力，但不复用与当前项目不匹配的路由和页面结构。

#### 5.2.2 一份检索结果服务两端

RAG 返回结果不能只是一段字符串上下文，还必须能直接生成前端引用展示对象，避免重复建模。

#### 5.2.3 引用归属于消息

citations 必须挂在 assistant 消息上，而不是挂在全局 store 会话状态上。

#### 5.2.4 优先最小可运行路径

本次优先返回单次完整回答，不在第一版中增加流式、复杂检索优化或语音链路迁移。

---

## 6. 后端设计

### 6.1 目录与文件职责

建议在当前后端中新增以下模块：

- `backend/src/app/services/llm_service.py`
  - 负责模型 client 初始化与聊天生成
- `backend/src/app/services/rag_service.py`
  - 负责知识库检索与 citations 提取
- `backend/src/app/schemas/interview.py`
  - 负责 interview chat 请求/响应模型定义
- `backend/src/app/api/interview.py`
  - 负责 HTTP 接口、参数校验、服务编排

并修改：

- `backend/src/app/core/config.py`
  - 扩展真实 LLM/RAG 配置项
- `backend/src/app/main.py`
  - 注册 interview router

### 6.2 API 设计

新增接口：

- `POST /api/interview/chat`

请求体：

```json
{
  "messages": [
    { "role": "interviewer", "content": "请介绍一下你做过的项目" }
  ],
  "mode": "text"
}
```

响应体：

```json
{
  "reply": {
    "id": "msg_xxx",
    "role": "assistant",
    "content": "你可以先从项目背景、职责和结果三个维度来回答。",
    "sources": [
      {
        "title": "projects.md",
        "url": "knowledge/projects.md",
        "snippet": "项目经历应突出背景、个人职责、关键难点与结果。",
        "kind": "knowledge"
      }
    ],
    "createdAt": "2026-05-22T12:00:00Z"
  }
}
```

### 6.3 Schema 设计

建议统一为以下语义模型：

```ts
interface MessageCitation {
  title: string
  url: string
  snippet: string
  kind: string
}

interface InterviewMessage {
  id: string
  role: 'interviewer' | 'assistant'
  content: string
  sources: MessageCitation[]
  createdAt: string
}
```

后端 Pydantic schema 应与上述字段一一对应，避免前端再做额外转换。

### 6.4 RAG 服务设计

旧项目 `rag_service.py` 当前只返回纯字符串上下文，这不足以满足当前前端需要。

当前项目中的 `rag_service` 应返回结构化结果：

```python
{
    "context_text": str,
    "citations": [
        {
            "title": str,
            "url": str,
            "snippet": str,
            "kind": str,
        }
    ],
}
```

字段语义：

- `context_text`：拼给模型的检索内容
- `citations`：返回给前端消息卡片下方展示
- `title`：来源标题、文件名或知识条目名称
- `url`：最小版可先返回知识源相对路径或附件链接
- `snippet`：与当前回答最相关的文本片段
- `kind`：固定或枚举化的来源类型，第一版可统一为 `knowledge`

### 6.5 LLM 服务设计

旧项目 `llm_service.py` 的结构可参考，但 system prompt 必须重写。

当前项目中的 prompt 目标应是：

- 始终以“候选人的 AI 面试分身”身份回答
- 优先基于真实资料作答
- 面试追问场景下保持简洁、专业、自然
- 资料不足时明确边界，不编造经历
- 文本模式下允许自然分段，但避免过长

保留的实现思路：

- 独立的 `ensure_client()`
- 环境变量驱动配置
- `history_messages + rag_context` 拼接输入

不保留的部分：

- 穿越火线客服语境
- 语音播报优化约束
- 只适配流式 callback 的接口形态

### 6.6 配置设计

当前 `backend/src/app/core/config.py` 中已有：

- `interview_model`
- `interview_mode`
- 若干火山配置占位

建议扩展为两类配置：

#### LLM 配置

- `interview_model`
- `ark_api_key`
- `ark_base_url`
- `ark_endpoint_id`

#### RAG 配置

- `kb_api_key`
- `kb_project_name`
- `kb_collection_name`
- `kb_domain`

命名可以按当前项目习惯调整，但语义上应与旧项目环境变量尽量一致，降低迁移成本。

### 6.7 错误处理原则

最小版只处理必要边界：

- 缺少模型配置时返回明确错误
- 知识库检索失败时允许降级为无引用回答
- 无有效用户消息时拒绝请求

不在本次引入复杂重试、熔断或多模型回退。

---

## 7. 前端设计

### 7.1 改动范围

当前前端核心接入点包括：

- `frontend/src/store/interview/types.ts`
- `frontend/src/store/interview/api.ts`
- `frontend/src/store/interview/index.ts`
- `frontend/src/pages/interview/components/TerminalChatPanel.vue`
- `frontend/src/pages/interview/InterviewPage.vue`

### 7.2 不迁移旧项目前端

旧项目的前端主要围绕 RTC 语音房间与场景调用展开，不适合当前终端式面试页。

因此本次不迁移旧项目前端页面，而是：

- 保留当前页面结构
- 只接入旧项目后端能力对应的当前 API
- 将真实回答与 citations 映射到现有消息流

### 7.3 API 适配

`frontend/src/store/interview/api.ts` 应实现面向当前后端的 chat 请求方法。

发送内容：

- 当前消息列表中的必要历史
- 当前模式 `mode`

接收内容：

- `reply.content`
- `reply.sources`
- `reply.createdAt`

### 7.4 Store 适配

`frontend/src/store/interview/index.ts` 的 `send()` 流程改为：

1. 先插入 interviewer 消息
2. 更新发送中状态
3. 调用真实 chat API
4. 接收到 `reply` 后直接 push assistant 消息
5. assistant 消息保留 `sources`
6. 失败时更新错误态或回退状态

本次不再为引用维护额外会话级镜像状态。

### 7.5 消息渲染

`TerminalChatPanel.vue` 负责在 assistant 消息下渲染 citations。

展示规则：

- 仅 assistant 消息展示
- 仅 `sources.length > 0` 时展示
- 每条 citation 展示：
  - 标题
  - 链接
  - 摘要片段

展示风格延续当前 terminal 风格，不额外重做整页视觉。

---

## 8. 数据流设计

### 8.1 请求流

前端发送：

1. 用户输入问题
2. store 组装 `messages`
3. 调用 `POST /api/interview/chat`

后端处理：

1. 提取最后一条 interviewer 消息
2. 以其作为 query 检索知识库
3. 生成 `context_text` 与 `citations`
4. 调用模型生成回答
5. 组装 assistant reply

前端接收：

1. 将 assistant reply 插入消息列表
2. 根据 `sources` 渲染消息下方引用区

### 8.2 为什么引用与消息绑定

因为多轮面试追问中，引用来源必须属于某一条回答，否则用户很难判断当前 sources 到底对应哪一轮消息。

这也与当前项目已有 citations 设计方向保持一致。

---

## 9. 测试与验收

### 9.1 后端验收

至少验证：

- 健康启动成功
- `/api/interview/chat` 可接受合法请求
- 有知识库命中时返回 `reply.sources`
- 检索失败时仍能返回基本回答或明确错误
- 返回字段与前端预期一致

### 9.2 前端验收

至少验证：

- 页面发送消息后会请求真实后端
- assistant 消息可以展示回答内容
- assistant 消息下方可以展示 citations
- 无 citations 时引用区不显示
- 发送状态与错误状态不会破坏页面主流程

### 9.3 联调验收标准

本次改造完成后，用户应能在当前 AI 面试页完成如下完整流程：

1. 输入一条面试问题
2. 后端基于资料检索并生成回答
3. 页面显示 assistant 回复
4. 回复下方显示对应引用来源

只要这条链路稳定跑通，即视为最小可用版成立。

---

## 10. 后续演进方向

在本次最小版跑通后，可以再逐步考虑：

- 流式返回
- 语音模式接统一 chat 主链路
- 更丰富的 citations 展示
- 更细的来源类型区分
- 检索排序优化
- session summary / layered memory 接入

这些都应建立在本次“单次文字问答 + 引用展示”链路稳定之后。
