import type { InterviewMessage, SourceTag } from './types'

export interface ChatDraft {
  reply: InterviewMessage
  topic: string
  activeSources: SourceTag[]
}

const mockReplies: Array<{
  match: RegExp
  topic: string
  sources: SourceTag[]
  content: string
}> = [
  {
    match: /(项目|project|trade-off|架构|architecture)/i,
    topic: '项目细节追问',
    sources: [
      { label: '项目架构', kind: 'project' },
      { label: '复盘笔记', kind: 'note' },
    ],
    content:
      '如果面试官继续追问项目，我会按背景、约束、决策、结果这条线来回答，重点突出为什么这样设计，以及我在取舍里承担了什么判断。',
  },
  {
    match: /(自我介绍|introduce|yourself|background|经历)/i,
    topic: '自我介绍开场',
    sources: [
      { label: '简历摘要', kind: 'resume' },
      { label: '面试开场话术', kind: 'memory' },
    ],
    content:
      '自我介绍我会压缩成一条清晰路径：我做过什么、擅长解决什么问题、最能体现判断力的项目是什么，再自然引到后面的深挖问题。',
  },
]

const defaultReply = {
  topic: '技术话题延展',
  sources: [
    { label: '项目亮点', kind: 'project' as const },
    { label: '工程笔记', kind: 'note' as const },
  ],
  content:
    '当前阶段先用本地 mock 数据固定展示结构，主要验证页面层级、消息流节奏、状态切换以及文字模式和语音模式的共存入口。',
}

export const createMockReply = async (message: string): Promise<ChatDraft> => {
  const matched = mockReplies.find((item) => item.match.test(message))
  const payload = matched ?? defaultReply

  await new Promise((resolve) => setTimeout(resolve, 700))

  return {
    topic: payload.topic,
    activeSources: payload.sources,
    reply: {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: payload.content,
      sources: payload.sources,
      createdAt: new Date().toISOString(),
    },
  }
}
