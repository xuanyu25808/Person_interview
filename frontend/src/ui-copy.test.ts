import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { test } from 'node:test'
import assert from 'node:assert/strict'

const files = [
  'src/pages/interview/InterviewPage.vue',
  'src/pages/interview/components/TerminalTopBar.vue',
  'src/pages/interview/components/TerminalChatPanel.vue',
  'src/pages/interview/components/TerminalStatusPanel.vue',
  'src/pages/interview/components/TerminalBottomBar.vue',
  'src/store/interview/index.ts',
  'src/store/interview/mock.ts',
]

const read = (relativePath: string) => readFileSync(resolve(process.cwd(), relativePath), 'utf-8')

test('interview page uses Chinese product copy and avoids the old English hero text', () => {
  const combined = files.map(read).join('\n')

  assert.match(combined, /文字模式/)
  assert.match(combined, /语音模式/)
  assert.match(combined, /请输入你的面试问题/)
  assert.match(combined, /AI 面试分身/)
  assert.doesNotMatch(combined, /AI Interview Twin/)
  assert.doesNotMatch(combined, /Text mode/)
  assert.doesNotMatch(combined, /Voice mode/)
  assert.doesNotMatch(combined, /New interview/)
})
