// Screen 6: Opportunity Watch. Tell us what changed; the engine re-runs and lists what got better.
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TierBadge } from '../components/TierBadge'
import { Button, EmptyState, ErrorState, Icon, Loading, NeedProfile, PageTitle } from '../components/ui'
import { api } from '../lib/api'
import { formatDate } from '../lib/format'
import { hasBasics, useStore } from '../lib/store'
import type { Profile, Status, Tier, WatchNote } from '../lib/types'

const TIER_OF: Record<Status, Tier> = {
  ELIGIBLE: 'ready', LIKELY: 'likely', NEAR_MISS: 'one_step', NOT_ELIGIBLE: 'not_now', WATCHLIST: 'watchlist', NOT_APPLICABLE: 'hidden',
}

// Changes a merchant can report with one tap. Each is offered only while it is still "no".
const CHANGES: { key: string; when: (p: Profile) => boolean; apply: Profile }[] = [
  { key: 'udyam', when: (p) => p.udyam_registered === false, apply: { udyam_registered: true } },
  { key: 'pan', when: (p) => p.pan_available === false, apply: { pan_available: true } },
  { key: 'vending', when: (p) => p.business_activity === 'street_vending' && p.has_vending_proof === false, apply: { has_vending_proof: true } },
]

export default function Watch() {
  const { t, lang, profile, profileId, update, save } = useStore()
  const [notes, setNotes] = useState<WatchNote[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [lastCount, setLastCount] = useState<number | null>(null)

  const refresh = useCallback(async (id: string) => {
    try {
      setNotes((await api.watch(id)).notifications)
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    }
  }, [])

  useEffect(() => {
    if (profileId) void refresh(profileId)
    else setNotes([])
  }, [profileId, refresh])

  if (!hasBasics(profile)) return <NeedProfile />

  const report = async (changes: Profile) => {
    setBusy(true)
    setLastCount(null)
    try {
      // Make sure the "before" state is saved, then save the change so the backend can compare.
      if (!profileId) await save()
      const next = { ...profile, ...changes }
      const out = await save(next)
      update(changes)
      setLastCount(out.notifications.length)
      await refresh(out.profileId)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const available = CHANGES.filter((c) => c.when(profile))

  return (
    <>
      <PageTitle title={t('watch.title')} lead={t('watch.lead')} />

      <section className="card p-5 sm:p-8">
        <h2 className="text-xl">{t('watch.changed')}</h2>
        {available.length === 0 ? <p className="mt-2 text-muted-foreground">{t('watch.no_changes')}</p> : (
          <div className="mt-3 flex flex-wrap gap-2">
            {available.map((c) => <Button key={c.key} disabled={busy} onClick={() => report(c.apply)}>{t(`watch.change.${c.key}`)}</Button>)}
          </div>
        )}
        <p className="mt-3 text-sm text-muted-foreground">{t('watch.edit')} <Link to="/" className="link">{t('nav.profile')}</Link></p>
        <p role="status" className="mt-2 font-semibold text-success">
          {busy ? t('watch.checking') : lastCount === null ? '' : lastCount > 0 ? t('watch.result', { count: lastCount }) : t('watch.result_none')}
        </p>
      </section>

      <h2 className="mt-7 text-xl">{t('watch.feed')}</h2>
      {error && <ErrorState message={error} onRetry={profileId ? () => refresh(profileId) : undefined} />}
      {!notes && !error && <Loading />}
      {notes && notes.length === 0 && <div className="mt-3"><EmptyState title={t('watch.empty')}><p>{t('watch.empty_help')}</p></EmptyState></div>}
      {notes && notes.length > 0 && (
        <ul className="card mt-3 divide-y divide-border px-5">
          {notes.map((n) => (
            <li key={n.id} className="py-3">
              <p className="flex flex-wrap items-center gap-2">
                <Link to={`/scheme/${n.scheme_id}`} className="font-semibold link">{n.short_name}</Link>
                <span className="text-muted-foreground">{t(`watch.kind.${n.kind}`)}</span>
              </p>
              <p className="mt-1 flex flex-wrap items-center gap-2">
                <TierBadge tier={TIER_OF[n.old]} /><Icon name="back" className="h-4 w-4 rotate-180 text-muted-foreground" /><TierBadge tier={TIER_OF[n.new]} />
              </p>
              {n.created_at && <p className="mt-1 text-sm text-muted-foreground">{formatDate(n.created_at, lang)}</p>}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
