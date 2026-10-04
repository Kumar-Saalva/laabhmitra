// App state: language, consent, the merchant profile and the latest engine result.
// The profile lives in this browser (localStorage) and on our backend once consent is given.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { makeT, type Translate } from '../i18n'
import { api } from './api'
import type { Evaluation, Lang, Profile, WatchNote } from './types'

interface Saved { lang: Lang; consent: boolean; profile: Profile; profileId: string | null; skipped: string[] }

const KEY = 'laabhmitra.v1'
const EMPTY: Saved = { lang: 'en', consent: false, profile: {}, profileId: null, skipped: [] }

function load(): Saved {
  try {
    return { ...EMPTY, ...JSON.parse(localStorage.getItem(KEY) ?? '{}') }
  } catch {
    return EMPTY
  }
}

interface Store extends Saved {
  t: Translate
  evaluation: Evaluation | null
  loading: boolean
  error: string | null
  setLang: (lang: Lang) => void
  giveConsent: () => void
  update: (changes: Profile) => void
  replaceProfile: (profile: Profile) => void
  skip: (field: string) => void
  save: (profile?: Profile, fresh?: boolean) => Promise<{ profileId: string; notifications: WatchNote[] }>
  reset: () => void
  retry: () => void
}

const Ctx = createContext<Store | null>(null)

export function StoreProvider({ children }: { children: ReactNode }) {
  const [saved, setSaved] = useState<Saved>(load)
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const latest = useRef(0)

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(saved)) } catch { /* private mode: keep going in memory */ }
    document.documentElement.lang = saved.lang
  }, [saved])

  // Re-run the engine whenever the profile or language changes.
  const profileJson = JSON.stringify(saved.profile)
  useEffect(() => {
    const call = ++latest.current
    setLoading(true)
    api.evaluate(JSON.parse(profileJson), saved.lang)
      .then((result) => { if (call === latest.current) { setEvaluation(result); setError(null) } })
      .catch((e: Error) => { if (call === latest.current) setError(e.message) })
      .finally(() => { if (call === latest.current) setLoading(false) })
  }, [profileJson, saved.lang, attempt])

  // fresh = true saves as a new profile (used when a demo persona replaces the current one).
  const save = useCallback(async (profile?: Profile, fresh = false) => {
    const toSave = profile ?? saved.profile
    const consent = { given: true, purposes: ['eligibility_check'] }
    const out = await api.saveProfile({ ...toSave, consent }, fresh ? null : saved.profileId)
    setSaved((s) => ({ ...s, profileId: out.profile_id }))
    return { profileId: out.profile_id, notifications: out.notifications }
  }, [saved.profile, saved.profileId])

  const value = useMemo<Store>(() => ({
    ...saved,
    t: makeT(saved.lang),
    evaluation, loading, error,
    setLang: (lang) => setSaved((s) => ({ ...s, lang })),
    giveConsent: () => setSaved((s) => ({ ...s, consent: true })),
    update: (changes) => setSaved((s) => ({ ...s, profile: { ...s.profile, ...changes } })),
    replaceProfile: (profile) => setSaved((s) => ({ ...s, profile, profileId: null, skipped: [] })),
    skip: (field) => setSaved((s) => ({ ...s, skipped: [...s.skipped, field] })),
    save,
    reset: () => setSaved((s) => ({ ...EMPTY, lang: s.lang, consent: s.consent })),
    retry: () => setAttempt((n) => n + 1),
  }), [saved, evaluation, loading, error, save])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useStore(): Store {
  const store = useContext(Ctx)
  if (!store) throw new Error('useStore must be used inside StoreProvider')
  return store
}

export const hasBasics = (profile: Profile) => Boolean(profile.state && profile.business_activity)
