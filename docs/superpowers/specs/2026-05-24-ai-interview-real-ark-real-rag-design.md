# AI 面试分身真实 Ark / 真实知识库检索严格接入设计

## 1. 目标

本次改造的目标是在当前 AI 面试分身项目中同时接入：

1. 真实 Ark 大模型调用
2. 真实外部知识库检索能力
3. 严格基于检索依据回答的问答链路

本次不是继续扩展 mock 或本地占位回答，而是把当前已经跑通的前后端消息链路升级为真实的“检索 -> 生成 -> 引用返回”生产式最小闭环。

本次最关键的约束是：**一定要有依据，否则不回答。**

这意味着：

- RAG 检索失败时，接口应失败，不允许伪造回答
- RAG 无有效证据时，接口应失败，不允许调用 LLM 生成无依据内容
- LLM 只在已有检索证据的前提下执行生成
- 前端不能再用“看起来像回答”的兜底文本冒充真实结果

---

## 2. 范围

### 2.1 本次包含

- 在当前 `backend` 中把 `llm_service.py` 从占位实现替换为真实 Ark client 调用
- 在当前 `backend` 中把 `rag_service.py` 从本地 markdown 检索替换为真实知识库 API 调用
- 保持当前 `POST /api/interview/chat` 契约不变
- 保持当前前端 assistant 消息 + citations 展示结构不变
- 将错误语义从“尽量返回占位回答”调整为“无证据即失败”
- 让前端明确展示真实失败，而不是静默生成兜底回复

### 2.2 本次不包含

- 流式 SSE 返回
- 语音模式打通真实链路
- 多知识库切换
- rerank、多路召回、复杂检索优化
- 长期 memory 系统
- 旧项目 RTC / 语音房间 / scene 体系迁移

---

## 3. 背景与当前状态

当前项目已经完成第一阶段最小链路：

- 前端聊天页已改为请求真实 `POST /api/interview/chat`
- 后端已使用统一消息模型返回 `reply`
- assistant 消息已能携带 `sources`
- 前端已能在消息下方展示 citations

但当前 LLM / RAG 仍然是占位实现：

- `backend/src/app/services/llm_service.py`
  - 仍然返回本地拼接文本，不是真实 Ark 响应
- `backend/src/app/services/rag_service.py`
  - 仍然依赖本地 `knowledge/*.md` 检索，不是真实外部知识库

因此当前链路虽然结构正确，但仍不满足“真实接入”的要求。

---

## 4. 关键产品约束

### 4.1 回答必须可追溯

每一条 assistant 回答都必须绑定明确的来源证据，并以 citations 形式返回前端。

### 4.2 无证据不得回答

如果无法从知识库中取到可用证据，系统应明确失败，而不是：

- 编造候选人经历
- 输出看似合理的泛化话术
- 用默认提示文案冒充回答

### 4.3 先检索，后生成

生成不是主入口，检索才是门槛。只有检索成功且结果可用时，才允许调用大模型。

### 4.4 前端不得伪装成功

前端不能在后端失败时自己补一条“助手消息”假装本轮回答完成，而应展示真实失败信息。

---

## 5. 方案选择

本次考虑三种方式：

### 方案 A：只接真实 LLM，RAG 暂时保留本地检索

优点：

- 改动较小
- 可以较快拿到真实模型输出

缺点：

- 证据链仍然不真实
- 不满足“真实知识库接入”的目标
- 后续还要再拆一次 RAG 改造

### 方案 B：只接真实知识库，LLM 先保留占位生成

优点：

- 可先确认检索链路
- 有利于调试知识库返回结构

缺点：

- 无法完成完整真实问答闭环
- 用户看到的回答仍不是真实模型生成

### 方案 C：真实 Ark 与真实知识库一起接入，并执行严格失败策略（推荐）

优点：

- 一次打通真实闭环
- 行为约束最清晰
- 与“必须有依据才能回答”的目标一致

缺点：

- 集成面更大
- 联调时需要同时确认模型与知识库配置

### 结论

采用方案 C：**真实 Ark 与真实知识库一起接入，并执行严格失败策略。**

---

## 6. 总体架构

### 6.1 主链路

最终问答主链路如下：

1. 前端发送 `messages` 与 `mode`
2. 后端校验请求体，并提取最后一条 `interviewer` 消息作为 query
3. 后端先调用 `rag_service.retrieve(query)`
4. `rag_service` 访问真实知识库接口，返回：
   - `context_text`
   - `citations`
5. 如果 RAG 失败、超时、配置缺失、结果为空或无有效证据，直接返回错误
6. 只有在 RAG 成功且结果可用时，后端才调用 `llm_service.generate_reply(...)`
7. `llm_service` 调用真实 Ark 模型，结合历史消息与 `context_text` 生成回答
8. 后端组装统一 `reply`，附带 `sources`
9. 前端将 assistant 消息插入消息流，并展示 citations
10. 如果后端报错，前端展示真实错误状态，不补假回答

### 6.2 设计原则

#### 6.2.1 Evidence First

整个链路必须由证据驱动，而不是由模型先生成、再尝试解释来源。

#### 6.2.2 Contract Stable

前后端当前已经跑通的消息契约保持不变，避免在接入真实能力时再次扩大联调面。

#### 6.2.3 Failure Explicit

失败必须显式暴露给调用方，而不是在服务端或前端静默降级成貌似成功的结果。

#### 6.2.4 Service Boundary Clear

- API 层只负责校验和返回 HTTP 结果
- `answer_pipeline` 负责编排顺序与业务门槛
- `rag_service` 负责证据获取
- `llm_service` 负责文本生成

---

## 7. 后端设计

### 7.1 文件职责

本次主要围绕以下文件改造：

- `backend/src/app/services/llm_service.py`
  - 替换占位生成逻辑，接入真实 Ark client
- `backend/src/app/services/rag_service.py`
  - 替换本地 markdown 检索，接入真实知识库 API
- `backend/src/app/services/answer_pipeline.py`
  - 强化为严格“先检索、后生成”的编排层
- `backend/src/app/api/interview.py`
  - 维持 HTTP 契约，统一处理失败映射
- `backend/src/app/core/config.py`
  - 使用现有 Ark / KB 配置字段，补足真实接入所需校验

### 7.2 API 契约

继续保留现有接口：

- `POST /api/interview/chat`

请求体保持不变：

```json
{
  "messages": [
    { "role": "interviewer", "content": "请介绍一下你做过的项目" }
  ],
  "mode": "text"
}
```

成功响应保持不变：

```json
{
  "reply": {
    "id": "msg_xxx",
    "role": "assistant",
    "content": "...",
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

失败时不再返回伪造 `reply`，而是返回明确错误码与错误信息。

### 7.3 answer_pipeline 编排规则

`build_answer(messages)` 的业务规则调整为：

1. 校验至少存在一条 `interviewer` 消息
2. 取最后一条 `interviewer` 消息内容作为 query
3. 调用 `rag_service.retrieve(query)`
4. 若返回结果不满足以下任一条件，则直接失败：
   - `context_text` 非空
   - `citations` 非空
   - citations 中至少有一条有效 `snippet`
5. RAG 通过后，再调用 `llm_service.generate_reply(messages, rag_context)`
6. 若 LLM 失败，则直接失败
7. 成功时组装 assistant `InterviewMessage`

这里的关键点是：**LLM 调用不能早于 RAG 成功。**

### 7.4 RAG 服务设计

`rag_service.py` 需要从“本地文档检索器”升级为“真实知识库客户端”。

#### 输入

- `query: str`

#### 输出

继续保持：

```python
@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    snippet: str
    kind: str = "knowledge"

@dataclass(frozen=True)
class RagResult:
    context_text: str
    citations: list[Citation]
```

#### 行为要求

1. 使用当前配置中的：
   - `kb_api_key`
   - `kb_project_name`
   - `kb_collection_name`
   - `kb_domain`
2. 调用真实知识库检索接口
3. 从知识库响应中提取可用于模型的上下文文本
4. 从同一份响应中提取 citations
5. 若外部接口失败、超时、响应结构不合法、无结果、结果不可提炼为有效 citations，则抛出明确错误

#### 证据有效性判断

至少满足以下条件才可视为“有依据”：

- 至少 1 条 citation
- citation 的 `snippet` 非空
- `context_text` 非空

如果只拿到标题但没有可引用片段，不应放行。

### 7.5 LLM 服务设计

`llm_service.py` 需要从本地字符串拼接改为真实 Ark 调用。

#### 输入

- `history_messages: list[dict[str, str]]`
- `rag_context: str`

#### 输出

- `str`，即最终 assistant 文本内容

#### 行为要求

1. 使用当前配置中的：
   - `ark_api_key`
   - `ark_base_url`
   - `ark_endpoint_id`
2. `ensure_client()` 负责校验配置并初始化真实 client
3. 发送给 Ark 的消息中必须包含：
   - 面试分身 persona/system prompt
   - 历史消息
   - 检索到的 `rag_context`
4. 模型职责是：
   - 只基于已提供材料回答
   - 对问题进行面试场景下的自然表达
   - 不扩写不存在的经历

#### Prompt 约束

prompt 必须强调：

- 你是候选人的 AI 面试分身
- 只能依据提供的候选人资料回答
- 如果材料不足，不要补造未提供的信息
- 回答应简洁、自然、适合面试交流

虽然正常路径下“材料不足”应在 RAG 阶段就失败，但 prompt 仍需要保留这一安全边界。

### 7.6 配置设计

本次继续使用当前配置字段，不额外发明新命名：

#### LLM

- `interview_model`
- `ark_api_key`
- `ark_base_url`
- `ark_endpoint_id`

#### RAG

- `kb_api_key`
- `kb_project_name`
- `kb_collection_name`
- `kb_domain`

要求：

- 缺失配置时，在服务启动后首次调用时能返回明确错误
- 错误信息应能区分“模型配置缺失”与“知识库配置缺失”

### 7.7 错误语义

#### 422

请求体不合法时返回：

- 无 `messages`
- 无 `interviewer` 消息
- 字段类型不正确

#### 503

外部依赖不可用时返回：

- 知识库超时 / 失败
- Ark 调用超时 / 失败
- 上游返回不可用状态

#### 500

服务内部配置或实现问题时返回：

- 缺失必要配置
- 外部返回结构与当前解析逻辑不匹配
- 内部组装逻辑异常

重点不是穷举所有错误，而是保证：前端能区分“请求错了”与“服务依赖挂了”。

---

## 8. 前端设计

### 8.1 保持现有消息契约

本次不改动前端消息结构：

- `reply.content`
- `reply.sources`
- `reply.createdAt`

现有 citations 渲染组件继续复用。

### 8.2 API 层行为调整

`frontend/src/store/interview/api.ts` 应继续直接请求后端，但错误处理要更严格：

- 后端返回非 2xx 时，抛出可识别错误
- 不在 API 层伪造 assistant reply
- 不吞掉后端失败信息

### 8.3 Store 层行为调整

`frontend/src/store/interview/index.ts` 当前失败时会 push 一条“后端问答链路暂时不可用”的 assistant 消息。

这与新的严格策略不一致，需要调整为：

- 请求失败时保留 interviewer 消息
- 停止发送中状态
- 设置错误态 / 错误提示
- 不生成假的 assistant 回答

### 8.4 页面展示策略

用户在页面上应明确看见：

- 成功时：真实 assistant 回答 + citations
- 失败时：本轮请求失败提示

失败提示可以是页面已有错误区域，也可以是 store 暴露的错误文本，但不应表现成正常消息内容。

---

## 9. 数据流

### 9.1 成功路径

1. 用户输入问题
2. 前端发送 `messages`
3. 后端做请求校验
4. 后端执行 RAG 检索
5. RAG 返回有效 `context_text + citations`
6. 后端执行 Ark 生成
7. 组装 assistant reply
8. 前端渲染回答与引用

### 9.2 失败路径

#### RAG 失败

1. 用户输入问题
2. 前端发送请求
3. 后端执行 RAG
4. RAG 失败 / 无证据
5. 后端直接返回错误
6. 前端展示错误提示
7. 不插入 assistant 伪回答

#### LLM 失败

1. RAG 已成功
2. Ark 调用失败
3. 后端返回错误
4. 前端展示错误提示
5. 不插入 assistant 伪回答

---

## 10. 测试与验收

### 10.1 后端测试

至少覆盖以下场景：

1. 合法请求 + 有证据 + LLM 成功 -> 返回 `200` 与结构化 `reply`
2. 请求中没有 interviewer 消息 -> 返回 `422`
3. RAG 返回空结果 -> 返回失败，不生成回答
4. RAG 调用异常 -> 返回失败，不生成回答
5. LLM 调用异常 -> 返回失败
6. 成功响应中 `sources` 非空，且 `snippet` 有值

### 10.2 前端测试

至少覆盖以下场景：

1. API 成功时按现有契约解析 `reply`
2. API 失败时抛出错误，不伪造成功返回
3. store 在失败时不追加 assistant 假消息
4. assistant 成功消息仍正常渲染 citations

### 10.3 联调验收标准

本次改造完成后，必须满足：

1. 页面发送问题后，会命中真实后端
2. 后端先走真实知识库检索，再走真实 Ark 生成
3. 页面展示的回答来自真实模型输出
4. 每条回答带有真实 citations
5. 当知识库失败或无依据时，页面明确失败，而不是出现无依据回答

只要这五点成立，才视为本阶段完成。

---

## 11. 实施边界

### 11.1 不做的事

本阶段不顺手做以下扩展：

- 把 `mode=voice` 一并打通
- 引入流式返回
- 做复杂 prompt 工程平台化
- 做多知识源聚合
- 做额外 UI 重构

### 11.2 允许的最小调整

如果真实 Ark / KB SDK 或 HTTP 接入要求对配置校验、错误包装、测试桩注入做最小辅助改造，可以做，但不得改变当前前后端主契约。

---

## 12. 后续演进方向

在本次严格真实链路稳定后，再考虑：

- 流式输出
- 更强的 citation 展示样式
- 检索排序优化
- 会话摘要与长期 memory
- 语音模式复用同一问答主链路

这些都必须建立在“有依据才能回答”的基础能力稳定之后。
