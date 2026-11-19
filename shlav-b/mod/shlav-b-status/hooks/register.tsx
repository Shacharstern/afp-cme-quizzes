import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'
import type { Snapshot } from '../types'

const PANE = 'shlav-b-status'
const TITLE = 'שלב ב׳ · נושאים'
const snap = atom({ plugin: 'shlav-b-status', key: 'snap' } as const, null, { shape: 'snap-1' })
const open = atom({ plugin: 'shlav-b-status', key: 'open' } as const, null, { shape: 'open-1' })
const SCRIPT = 'shlav-b/engine/status.py'
const ICON: Record<string, string> = { ok: '✓', warn: '!', fail: '✗', todo: '○' }
const COLOR: Record<string, string> = { ok: 'success', warn: 'warning', fail: 'error', todo: 'inactive' }
const JOB: Record<string, string> = { running: 'רץ', done: 'הסתיים', fail: 'נכשל', stalled: 'תקוע?' }

let busy = false
async function refresh($: EngineInterface) {
  if (busy) return
  busy = true
  try {
    if (!(await $.fs.exists(SCRIPT))) return
    const r = await $.process.run(['python3', SCRIPT], { timeoutMs: 60000 })
    const next: Snapshot = r.exitCode === 0
      ? JSON.parse(r.stdout)
      : { at: '', topics: [], jobs: [], error: (r.stderr || 'status.py failed').slice(-300) }
    await update($, snap, () => next)
    const running = next.jobs.filter(j => j.state === 'running').length
    const open_ = next.topics.reduce((n, t) => n + t.stages.filter(s => s.state === 'fail' || s.state === 'warn').length, 0)
    $.ui.status(running ? `שלב ב׳: ${running} עבודות רצות` : open_ ? `שלב ב׳: ${open_} פריטים פתוחים` : undefined)
  } catch (err) {
    await update($, snap, s => ({ at: s?.at ?? '', topics: s?.topics ?? [], jobs: s?.jobs ?? [], error: String(err).slice(0, 300) }))
  } finally {
    busy = false
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    await $.command.register({ name: 'shlav-b-status', description: 'Open the Shlav B topic status pane' })
    if (await $.fs.exists(SCRIPT)) {
      void $.ui.open({ id: PANE, title: TITLE })
      void refresh($)
      $.clock.every(6000, () => refresh($))
    }
    return started
  })

  on('command.run', { command: 'shlav-b-status' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE })
    await refresh($)
    return { text: 'נפתח חלון הסטטוס של שלב ב׳.' }
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (e.tool === 'Write' || e.tool === 'Edit' || e.tool === 'Bash') void refresh($)
    return ran
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button, Progress } = $.ui.resolve(e)
    const s = await read($, snap)
    const sel = await read($, open)
    if (!s) return <Box flexDirection="column"><Text dimColor>טוען סטטוס…</Text></Box>
    const jobs = s.jobs.filter(j => j.state !== 'done' || j.ageSec < 600)
    const shown = sel ?? s.topics.find(t => t.ok < t.total)?.id ?? s.topics[0]?.id
    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="row" gap={1}>
          <Text bold>נושאים בעבודה</Text>
          <Text dimColor>עודכן {s.at}</Text>
          <Button plain onPress={() => refresh($)}>רענן</Button>
        </Box>
        {s.error && <Text color="error">{s.error}</Text>}
        {jobs.length > 0 && (
          <Box flexDirection="column">
            <Text bold>עבודות</Text>
            {jobs.map(j => (
              <Text color={j.state === 'fail' ? 'error' : j.state === 'running' ? 'suggestion' : j.state === 'stalled' ? 'warning' : 'success'}>
                {j.state === 'running' ? '● ' : '  '}{j.name} · {JOB[j.state]} · {j.last}
              </Text>
            ))}
          </Box>
        )}
        {s.topics.length === 0 && <Text dimColor>אין עדיין נושאים בעבודה.</Text>}
        {s.topics.map(t => (
          <Box flexDirection="column" key={t.id}>
            <Button plain key={'topic-' + t.id} label={t.name} onPress={() => update($, open, cur => (cur === t.id ? null : t.id))}>
              <Text bold>{t.id === shown ? '▾ ' : '▸ '}{t.name}</Text> <Text dimColor>{t.ok}/{t.total}</Text>
            </Button>
            <Progress label={t.name} value={t.ok} max={t.total} valueText={`${t.ok}/${t.total}`}
              color={t.stages.some(x => x.state === 'fail') ? 'error' : t.ok === t.total ? 'success' : 'warning'} />
            {t.id === shown && t.stages.map(x => (
              <Box flexDirection="column" key={x.key}>
                <Text color={COLOR[x.state]}>{ICON[x.state]} {x.label}</Text>
                {x.detail !== '' && <Text dimColor>   {x.detail}</Text>}
                {x.state !== 'ok' && x.fix !== '' && <Text dimColor italic>   → {x.fix}</Text>}
              </Box>
            ))}
          </Box>
        ))}
      </Box>
    )
  })
}
