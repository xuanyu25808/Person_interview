import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TerminalChatPanel from './TerminalChatPanel.vue'
import type { InterviewMessage } from '../../../store/interview/types'

const createAssistantMessage = (overrides: Partial<InterviewMessage> = {}): InterviewMessage => ({
  id: 'assistant_1',
  role: 'assistant',
  content: '',
  sources: [],
  createdAt: '2026-05-26T12:00:00Z',
  state: 'streaming',
  thinking: null,
  ...overrides,
})

describe('TerminalChatPanel', () => {
  it('shows waiting status beside the streaming cursor before content arrives', () => {
    const wrapper = mount(TerminalChatPanel, {
      props: {
        messages: [createAssistantMessage()],
        statusLabel: '正在检索资料',
      },
    })

    expect(wrapper.text()).toContain('正在检索资料')
    expect(wrapper.find('.streaming-status').exists()).toBe(true)
    expect(wrapper.find('.streaming-cursor').exists()).toBe(true)
  })

  it('hides waiting status once streaming content arrives', () => {
    const wrapper = mount(TerminalChatPanel, {
      props: {
        messages: [createAssistantMessage({ content: '第一段' })],
        statusLabel: '正在生成回答',
      },
    })

    expect(wrapper.text()).not.toContain('正在生成回答')
    expect(wrapper.find('.streaming-status').exists()).toBe(false)
    expect(wrapper.find('.streaming-cursor').exists()).toBe(true)
  })

  it('does not render the thinking panel for assistant messages', () => {
    const wrapper = mount(TerminalChatPanel, {
      props: {
        messages: [
          createAssistantMessage({
            content: '回答内容',
            state: 'done',
            thinking: {
              phase: 'thinking',
              summary: '正在归纳与你问题最相关的证据，并组织回答重点。',
              updatedAt: '2026-05-26T12:00:01Z',
            },
          }),
        ],
      },
    })

    expect(wrapper.find('.message-thinking').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('AI 正在思考')
    expect(wrapper.text()).not.toContain('正在归纳与你问题最相关的证据，并组织回答重点。')
  })
})
