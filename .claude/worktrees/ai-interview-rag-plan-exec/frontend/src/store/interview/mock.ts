import type { InterviewMessage, MessageCitation } from './types'

export interface ChatDraft {
  reply: InterviewMessage
}

interface MockReply {
  match: RegExp
  sources: MessageCitation[]
  content: string
}

const mockReplies: MockReply[] = [
  {
    match: /(项目|project|trade-off|架构|architecture)/i,
    sources: [
      {
        title: 'projects.md',
        url: '/knowledge/projects.md',
        snippet: 'AI 面试分身项目重点是让回答基于真实资料，而不是通用大模型自由发挥。',
        kind: 'projects',
      },
      {
        title: 'notes.md',
        url: '/knowledge/notes.md',
        snippet: '如果继续追问架构取舍，回答应按背景、约束、决策和结果展开。',
        kind: 'notes',
      },
    ],
    content:
      '如果面试官继续追问项目，我会按背景、约束、决策、结果这条线来回答，重点突出为什么这样设计，以及我在取舍里承担了什么判断。',
  },
  {
    match: /(自我介绍|introduce|yourself|background|经历)/i,
    sources: [
      {
        title: 'resume.md',
        url: '/knowledge/resume.md',
        snippet: '自我介绍要压缩成一条清晰路径：做过什么、擅长什么、代表项目是什么。',
        kind: 'resume',
      },
      {
        title: 'interview_qa.md',
        url: '/knowledge/interview_qa.md',
        snippet: '开场回答应自然引到后续深挖问题，而不是停留在流水账描述。',
        kind: 'interview_qa',
      },
    ],
    content:
      '自我介绍我会压缩成一条清晰路径：我做过什么、擅长解决什么问题、最能体现判断力的项目是什么，再自然引到后面的深挖问题。',
  },
]

const defaultReply = {
  sources: [
    {
      title: 'projects.md',
      url: '/knowledge/projects.md',
      snippet: '当前阶段重点是验证聊天页结构、消息流节奏、状态切换以及语音与文字模式的共存。',
      kind: 'projects',
    },
    {
      title: 'notes.md',
      url: '/knowledge/notes.md',
      snippet: '回答需要绑定到具体来源，避免全局状态和消息状态重复建模。',
      kind: 'notes',
    },
  ],
  content:
    '当前阶段先用本地 mock 数据固定展示结构，主要验证页面层级、消息流节奏、状态切换以及文字模式和语音模式的共存入口。',
}

export const createMockReply = async (message: string): Promise<ChatDraft> => {
  const matched = mockReplies.find((item) => item.match.test(message))
  const payload = matched ?? defaultReply

  await new Promise((resolve) => setTimeout(resolve, 700))

  return {
    reply: {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: payload.content,
      sources: payload.sources,
      createdAt: new Date().toISOString(),
    },
  }
}
