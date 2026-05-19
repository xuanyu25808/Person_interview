# Voice Service Boundary

`services/voice` will承接现有火山引擎实时语音项目，用于复用已有的实时语音能力。

## Responsibility split

- `backend` 负责 persona / retrieval / memory / answer generation
- `services/voice` 负责 ASR / TTS / 音频传输
- 文字模式和语音模式必须共享同一个 `session_id` 与会话上下文

## Phase-one note

This directory is a boundary placeholder only in phase one. Real voice integration is intentionally deferred.
