export type Stage = { key: string; label: string; state: 'ok' | 'warn' | 'fail' | 'todo'; detail: string; fix: string }
export type TopicStatus = { id: string; name: string; ok: number; total: number; stages: Stage[] }
export type Job = { name: string; last: string; ageSec: number; state: 'running' | 'done' | 'fail' | 'stalled' }
export type Snapshot = { at: string; topics: TopicStatus[]; jobs: Job[]; error?: string }

declare module 'claude-code' {
  interface PluginState {
    'shlav-b-status': { snap: Shaped<Snapshot | null>; open: Shaped<string | null> }
  }
}
