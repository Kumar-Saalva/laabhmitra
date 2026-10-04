// One small wrapper around fetch. All calls go to our own backend under /api.
import type {
  Affordability, Evaluation, Explanation, Lang, PackPreview, Profile, ProjectReport, RuleTest, TrackerStatus, WatchNote,
} from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    })
  } catch {
    throw new Error('offline')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

const post = <T,>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  personas: () => request<Record<string, Profile & { display_name: string; story: string }>>('/api/personas'),
  schemes: () => request<{ id: string; short_name: string }[]>('/api/schemes'),
  scheme: (id: string) => request<Record<string, unknown>>(`/api/schemes/${id}`),
  evaluate: (profile: Profile, lang: Lang) => post<Evaluation>('/api/evaluate', { profile, lang }),
  extract: (text: string, lang: Lang) => post<{ profile: Profile; provider: string }>('/api/extract', { text, lang }),
  saveProfile: (profile: Record<string, unknown>, profile_id: string | null) =>
    post<{ profile_id: string; notifications: WatchNote[] }>('/api/profiles', { profile, profile_id }),
  explain: (profile: Profile, scheme_id: string, lang: Lang, kind: 'why' | 'why_not') =>
    post<Explanation>('/api/explain', { profile, scheme_id, lang, kind }),
  packPreview: (profile: Profile, profile_id: string | null, scheme_id: string, lang: Lang) =>
    post<PackPreview>('/api/pack/preview', { profile, profile_id, scheme_id, lang }),
  packStatus: (profile_id: string, scheme_id: string, status: TrackerStatus, amount_received_inr: number | null) =>
    post<{ status: TrackerStatus; amount_received_inr: number | null }>('/api/pack/status', {
      profile_id, scheme_id, status, amount_received_inr,
    }),
  affordability: (profile: Profile, scheme_id: string, annual_rate: number, tenure_months: number) =>
    post<Affordability>('/api/affordability', { profile, scheme_id, annual_rate, tenure_months }),
  projectReport: (profile: Record<string, unknown>) => post<ProjectReport>('/api/project-report', { profile }),
  async projectReportPdf(profile_id: string): Promise<Blob> {
    const response = await fetch(`/api/project-report/${profile_id}/pdf`)
    if (!response.ok) throw new Error(`Request failed (${response.status})`)
    return response.blob()
  },
  watch: (profile_id: string) => request<{ notifications: WatchNote[] }>(`/api/watch/${profile_id}`),
  testScheme: (scheme: unknown) => post<RuleTest>('/api/admin/test-scheme', { scheme }),

  async packPdf(profile: Profile, scheme_id: string, lang: Lang): Promise<Blob> {
    const response = await fetch('/api/pack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile, scheme_id, lang }),
    })
    if (!response.ok) throw new Error(`Request failed (${response.status})`)
    return response.blob()
  },
}
