# AI Interview Twin

This project is a single-page AI interview twin rather than a multi-page personal center.

It is designed for interview-style interaction through both text and voice, so an interviewer can talk directly with a grounded digital version of the candidate.

## Scope

- Single-page AI interview twin experience
- Text interview interaction
- Voice interview interaction
- Grounded answers based on curated candidate materials

## Directory roles

- `frontend/`: the frontend single-page entry for the AI interview twin
- `backend/`: the backend boundary for future persona, retrieval, memory, and answer generation work
- `knowledge/`: curated knowledge sources such as resume, projects, notes, and interview QA materials
- `services/voice/`: the voice boundary layer for ASR, TTS, and audio transport

## Current phase

The current phase only establishes the directory structure and minimal skeleton for the single-page product direction. Full chat UI, backend interview APIs, memory logic, and real voice integration are intentionally not implemented yet.
