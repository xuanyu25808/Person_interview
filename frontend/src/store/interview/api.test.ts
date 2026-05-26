import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

import { sendInterviewMessage, streamInterviewMessage } from './api'
import { createPinia, setActivePinia } from 'pinia'
import { useInterviewStore } from './index'

const createStreamResponse = (frames: string[]) => {
  const encoder = new TextEncoder()
  let index = 0

  return {
    ok: true,
    body: {
      getReader: () => ({
        read: async () => {
          if (index >= frames.length) {
            return { done: true, value: undefined }
          }

          const value = encoder.encode(frames[index])
          index += 1
          return { done: false, value }
        },
      }),
    },
  }
}

describe('sendInterviewMessage', () => {
  beforeEach(() => {
    fetchMock.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('sends the new interview chat payload shape and returns structured reply', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      text: async () =>
        JSON.stringify({
          reply: {
            id: 'msg_1',
            role: 'assistant',
            content: '这是基于知识库生成的回答。',
            sources: [
              {
                title: 'projects.md',
                url: 'knowledge/projects.md',
                snippet: '候选人的项目经历覆盖检索与生成链路。',
                kind: 'knowledge',
              },
            ],
            createdAt: '2026-05-22T12:00:00Z',
            state: 'done',
            thinking: {
              phase: 'responding',
              summary: '已基于检索到的资料生成最终回答。',
              updatedAt: '2026-05-22T12:00:00Z',
            },
          },
        }),
    })

    const response = await sendInterviewMessage({
      messages: [
        { role: 'interviewer', content: '请介绍你的项目经历。' },
        { role: 'assistant', content: '好的。' },
      ],
      mode: 'text',
    })

    expect(fetchMock).toHaveBeenCalledWith('/api/interview/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [
          { role: 'interviewer', content: '请介绍你的项目经历。' },
          { role: 'assistant', content: '好的。' },
        ],
        mode: 'text',
      }),
    })

    expect(response.reply.content).toContain('知识库')
    expect(response.reply.sources).toHaveLength(1)
  })

  it('parses stream events from the interview stream endpoint', async () => {
    fetchMock.mockResolvedValue(
      createStreamResponse([
        'data: {"type":"status","status":"retrieving","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z"}\n\n',
        'data: {"type":"thinking","status":"thinking","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","thinking":{"phase":"thinking","summary":"正在归纳证据","updatedAt":"2026-05-25T12:00:01Z"}}\n\n',
        'data: {"type":"delta","status":"responding","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","delta":"第一段"}\n\n',
        'data: {"type":"sources","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","sources":[]}\n\n',
        'data: {"type":"done","status":"done","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z"}\n\n',
      ]),
    )

    const events: Array<Record<string, unknown>> = []

    await streamInterviewMessage(
      {
        messages: [{ role: 'interviewer', content: 'retrieval' }],
        mode: 'text',
      },
      (event) => {
        events.push(event as unknown as Record<string, unknown>)
      },
    )

    expect(fetchMock).toHaveBeenCalledWith('/api/interview/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        messages: [{ role: 'interviewer', content: 'retrieval' }],
        mode: 'text',
      }),
    })
    expect(events.map((event) => event.type)).toEqual(['status', 'thinking', 'delta', 'sources', 'done'])
  })

  it('throws stable error when backend returns empty body', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => '',
    })

    await expect(
      sendInterviewMessage({
        messages: [{ role: 'interviewer', content: '77' }],
        mode: 'text',
      }),
    ).rejects.toMatchObject({
      statusCode: 500,
      message: 'Interview chat request failed',
    })
  })
})

describe('useInterviewStore', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('streams assistant thinking, content, and sources into the placeholder message', async () => {
    fetchMock.mockResolvedValue(
      createStreamResponse([
        'data: {"type":"status","status":"retrieving","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z"}\n\n',
        'data: {"type":"thinking","status":"thinking","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","thinking":{"phase":"thinking","summary":"正在归纳证据","updatedAt":"2026-05-25T12:00:01Z"}}\n\n',
        'data: {"type":"delta","status":"responding","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","delta":"第一段"}\n\n',
        'data: {"type":"delta","status":"responding","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","delta":"第二段"}\n\n',
        'data: {"type":"sources","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","sources":[{"title":"projects.md","url":"knowledge/projects.md","snippet":"retrieval","kind":"knowledge"}]}\n\n',
        'data: {"type":"done","status":"done","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z"}\n\n',
      ]),
    )

    const store = useInterviewStore()
    await store.send('retrieval')

    expect(store.messages).toHaveLength(2)
    expect(store.messages[0].role).toBe('interviewer')
    expect(store.messages[1].role).toBe('assistant')
    expect(store.messages[1].thinking?.summary).toBe('正在归纳证据')
    expect(store.messages[1].content).toBe('第一段第二段')
    expect(store.messages[1].sources).toEqual([
      {
        title: 'projects.md',
        url: 'knowledge/projects.md',
        snippet: 'retrieval',
        kind: 'knowledge',
      },
    ])
    expect(store.messages[1].state).toBe('done')
    expect(store.status).toBe('idle')
  })

  it('marks the assistant done when the stream closes without a done event', async () => {
    fetchMock.mockResolvedValue(
      createStreamResponse([
        'data: {"type":"status","status":"retrieving","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z"}\n\n',
        'data: {"type":"thinking","status":"thinking","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","thinking":{"phase":"thinking","summary":"正在归纳证据","updatedAt":"2026-05-25T12:00:01Z"}}\n\n',
        'data: {"type":"delta","status":"responding","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","delta":"雷神是英雄级武器"}\n\n',
        'data: {"type":"sources","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","sources":[{"title":"weapon-guide.md","url":"knowledge/weapon-guide.md","snippet":"M4A1-雷神是热门英雄级步枪。","kind":"knowledge"}]}\n\n',
      ]),
    )

    const store = useInterviewStore()
    await store.send('雷神')

    expect(store.messages[1].content).toContain('雷神')
    expect(store.messages[1].sources).toHaveLength(1)
    expect(store.messages[1].state).toBe('done')
    expect(store.status).toBe('idle')
  })
  it('marks the assistant done when the stream closes without a done event', async () => {
    fetchMock.mockResolvedValue(
      createStreamResponse([
        'data: {"type":"status","status":"retrieving","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z"}\n\n',
        'data: {"type":"thinking","status":"thinking","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","thinking":{"phase":"thinking","summary":"正在归纳证据","updatedAt":"2026-05-25T12:00:01Z"}}\n\n',
        'data: {"type":"delta","status":"responding","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","delta":"雷神是英雄级武器"}\n\n',
        'data: {"type":"sources","replyId":"msg_stream","createdAt":"2026-05-25T12:00:00Z","sources":[{"title":"weapon-guide.md","url":"knowledge/weapon-guide.md","snippet":"M4A1-雷神是热门英雄级步枪。","kind":"knowledge"}]}\n\n',
      ]),
    )

    const store = useInterviewStore()
    await store.send('雷神')

    expect(store.messages[1].content).toContain('雷神')
    expect(store.messages[1].sources).toHaveLength(1)
    expect(store.messages[1].state).toBe('done')
    expect(store.status).toBe('idle')
  })

  it('keeps refusal replies on the normal assistant streaming path', async () => {
    fetchMock.mockResolvedValue(
      createStreamResponse([
        'data: {"type":"status","status":"retrieving","replyId":"msg_refusal","createdAt":"2026-05-25T12:00:00Z"}\n\n',
        'data: {"type":"thinking","status":"thinking","replyId":"msg_refusal","createdAt":"2026-05-25T12:00:00Z","thinking":{"phase":"thinking","summary":"没有足够依据","updatedAt":"2026-05-25T12:00:01Z"}}\n\n',
        'data: {"type":"delta","status":"responding","replyId":"msg_refusal","createdAt":"2026-05-25T12:00:00Z","delta":"我暂时没法基于现有资料给出可靠回答。"}\n\n',
        'data: {"type":"sources","replyId":"msg_refusal","createdAt":"2026-05-25T12:00:00Z","sources":[]}\n\n',
        'data: {"type":"done","status":"done","replyId":"msg_refusal","createdAt":"2026-05-25T12:00:00Z"}\n\n',
      ]),
    )

    const store = useInterviewStore()
    await store.send('77')

    expect(store.messages[1].content).toContain('我暂时没法基于现有资料给出可靠回答')
    expect(store.messages[1].sources).toEqual([])
    expect(store.messages[1].state).toBe('done')
    expect(store.errorMessage).toBe('')
  })
})
