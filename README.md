# 111AI 面试数字分身

这个项目是一个单页的 AI 面试数字分身，而不是一个多页面的个人中心。

它面向面试场景下的文本与语音互动，让面试官可以直接与一个基于真实资料构建的候选人数字化分身进行交流。

## 项目范围

- 单页 AI 面试数字分身体验
- 文本面试互动
- 语音面试互动
- 基于整理后的候选人资料给出有依据的回答

## 目录职责

- `frontend/`：AI 面试数字分身的前端单页入口
- `backend/`：后端边界层，后续用于承载 persona、检索、记忆与回答生成等能力
- `knowledge/`：整理后的知识资料来源，例如简历、项目材料、笔记与面试问答素材
- `services/voice/`：语音能力边界层，用于承载 ASR、TTS 与音频传输

## 当前阶段

当前阶段已经进入后端能力接入期。后端 Python 环境统一使用 `uv` 管理，避免全局解释器与项目依赖不一致。

## Backend commands

```bash
uv sync --directory backend
uv run --directory backend uvicorn app.main:app --app-dir src --reload
uv run --directory backend pytest
```




