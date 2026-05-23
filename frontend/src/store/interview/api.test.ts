import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

import { sendInterviewMessage } from './api'

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
      json: async () => ({
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
})
