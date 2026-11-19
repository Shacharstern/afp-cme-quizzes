import { expect, test } from 'claude-code/testing'

const SNAP = {
  at: '12:00:00',
  jobs: [{ name: 'vte-transcribe', last: '957 s 272 wall', ageSec: 5, state: 'running' }],
  topics: [{
    id: 'vte', name: 'DVT ו-PE', ok: 1, total: 2, stages: [
      { key: 'sweep', label: 'סריקת מקורות ב-Drive', state: 'warn', detail: '1 קבצים בלי החלטה', fix: 'לתת החלטה' },
      { key: 'pack', label: 'חבילה עברה בדיקה', state: 'ok', detail: '', fix: '' },
    ],
  }],
}
const PANE = {
  plugin: 'shlav-b-status', component: 'Pane', requestId: 'shlav-b-status',
  props: { title: 'x', isFocused: false, bodyColumns: 50, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
} as const

test('the pane shows jobs, topics and the first unfinished topic open', async ($, on) => {
  on('fs.exists', () => ({ value: true }))
  on('process.run', () => ({ value: { exitCode: 0, stdout: JSON.stringify(SNAP), stderr: '' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.status', () => ({ value: undefined }))
  on('command.register', () => ({ value: { command: 'shlav-b-status' } }))
  await $.command.run({ command: 'shlav-b-status', args: '' })
  for (const surface of ['desktop', 'mobile', 'terminal'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /vte-transcribe/ }))?.text).toContain('רץ')
    expect((await ui.find({ type: 'Text', text: /סריקת מקורות/ }))?.text).toBe('! סריקת מקורות ב-Drive')
    expect((await ui.find({ type: 'Text', text: /לתת החלטה/ }))?.text).toContain('→')
    await ui.unmount()
  }
})
