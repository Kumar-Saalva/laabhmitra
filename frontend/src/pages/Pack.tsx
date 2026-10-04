// Screen 5: application pack. Checklist (have / need), draft preview, PDF download, status tracker.
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { TierBadge } from '../components/TierBadge'
import { Button, ErrorState, Icon, Loading, NeedProfile, PageTitle } from '../components/ui'
import { api } from '../lib/api'
import { hasBasics, useStore } from '../lib/store'
import type { PackPreview, TrackerStatus } from '../lib/types'

const STEPS: TrackerStatus[] = ['not_started', 'docs_ready', 'applied', 'sanctioned', 'received']
const STATE_STYLE = { have: 'text-leaf bg-leaf-wash', need: 'text-sindoor bg-sindoor-wash', check: 'text-turmeric bg-turmeric-wash' }
const STATE_ICON = { have: 'check', need: 'cross', check: 'question' }

export default function Pack() {
  const { id = '' } = useParams()
  const { t, lang, profile, profileId, evaluation, save } = useStore()
  const [pack, setPack] = useState<PackPreview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<TrackerStatus>('not_started')
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  const profileJson = JSON.stringify(profile)
  useEffect(() => {
    if (!hasBasics(profile)) return
    let cancelled = false
    setPack(null)
    setError(null)
    api.packPreview(profile, profileId, id, lang)
      .then((p) => {
        if (cancelled) return
        setPack(p)
        setStatus(p.tracker?.status ?? 'not_started')
        setAmount(p.tracker?.amount_received_inr != null ? String(p.tracker.amount_received_inr) : '')
      })
      .catch((e: Error) => { if (!cancelled) setError(e.message) })
    return () => { cancelled = true }
  }, [id, lang, profileJson, profileId])

  if (!hasBasics(profile)) return <NeedProfile />
  if (error) return <ErrorState message={error} />
  if (!pack) return <Loading />
  const result = evaluation?.results.find((r) => r.scheme_id === id)

  const download = async () => {
    setDownloading(true)
    setNote(null)
    try {
      const url = URL.createObjectURL(await api.packPdf(profile, id, lang))
      const link = document.createElement('a')
      link.href = url
      link.download = `laabhmitra-${id}-draft.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      setNote(t('pack.download_failed'))
    } finally {
      setDownloading(false)
    }
  }

  const saveStatus = async (next: TrackerStatus, received = amount) => {
    setStatus(next)
    setNote(null)
    try {
      const pid = profileId ?? (await save()).profileId
      const rupees = next === 'received' && received.trim() ? Math.round(Number(received.replace(/,/g, ''))) : null
      await api.packStatus(pid, id, next, Number.isFinite(rupees as number) ? rupees : null)
      setNote(t('pack.status_saved'))
    } catch {
      setNote(t('pack.status_failed'))
    }
  }

  return (
    <>
      <PageTitle title={t('pack.title', { scheme: pack.scheme.short_name })} lead={t('pack.lead')} back={`/scheme/${id}`} />
      {result && <TierBadge tier={result.tier} />}
      {result && (result.tier === 'not_now') && <p className="mt-3 border-l-4 border-sindoor bg-sindoor-wash p-3 text-sm">{t('pack.not_now')}</p>}

      <section className="ledger mt-5 px-5 py-4">
        <h2 className="text-xl">{t('pack.checklist')}</h2>
        {pack.checklist.length === 0 ? <p className="mt-2 text-soft">{t('pack.no_documents')}</p> : (
          <ul className="mt-2 divide-y divide-rule/70">
            {pack.checklist.map((item) => (
              <li key={item.document} className="flex items-start gap-3 py-2.5">
                <span className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${STATE_STYLE[item.state]}`}>
                  <Icon name={STATE_ICON[item.state]} className="h-4 w-4" />
                </span>
                <div className="flex-1">
                  <p className="font-medium">{item.document}</p>
                  {item.note && <p className="text-sm text-soft">{item.note}</p>}
                </div>
                <span className="shrink-0 text-sm font-semibold">{t(`pack.state.${item.state}`)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="ledger mt-5 px-5 py-4">
        <h2 className="text-xl">{t('pack.draft')}</h2>
        <p className="text-sm text-soft">{t('pack.draft_note')}</p>
        <div className="relative mt-3 overflow-hidden border border-rule bg-white p-4">
          <span aria-hidden="true" className="pointer-events-none absolute inset-0 flex items-center justify-center text-center text-4xl font-bold text-sindoor/10 [transform:rotate(-24deg)] sm:text-6xl">DRAFT</span>
          <pre className="relative whitespace-pre-wrap font-sans text-[0.95rem]">{pack.draft.text}</pre>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button variant="primary" onClick={download} disabled={downloading}><Icon name="download" className="h-4 w-4" />{downloading ? t('state.loading') : t('pack.download')}</Button>
          {pack.scheme.application.url && (
            <a href={pack.scheme.application.url} target="_blank" rel="noreferrer" className="tap inline-flex items-center gap-1.5 rounded-md border border-ink/30 px-4 hover:border-ink">
              <Icon name="link" className="h-4 w-4" />{t('card.official')}
            </a>
          )}
        </div>
        <p className="mt-3 text-sm text-soft">{t('pack.never')}</p>
      </section>

      {id === 'pmegp' && profile.is_new_project === true && (
        <section className="ledger mt-5 px-5 py-4">
          <h2 className="text-xl">{t('project.title')}</h2>
          <p className="mt-1 max-w-[68ch]">{t('pack.project_note')}</p>
          <Link to="/project" className="tap mt-3 inline-flex items-center rounded-md bg-ink px-5 font-semibold text-sheet hover:bg-ink/90">{t('pack.project_open')}</Link>
        </section>
      )}

      <section className="ledger mt-5 px-5 py-4">
        <h2 className="text-xl">{t('pack.tracker')}</h2>
        <p className="text-sm text-soft">{t('pack.tracker_note')}</p>
        <ol className="mt-3 grid gap-2 sm:grid-cols-5">
          {STEPS.map((step, n) => {
            const done = STEPS.indexOf(status) >= n
            return (
              <li key={step}>
                <button type="button" onClick={() => saveStatus(step)} aria-pressed={status === step}
                  className={`tap flex w-full items-center gap-2 rounded-md border px-3 text-left ${status === step ? 'border-ink bg-ink text-sheet' : done ? 'border-leaf bg-leaf-wash' : 'border-ink/30 hover:border-ink'}`}>
                  <span className="figure">{n + 1}</span>{t(`pack.step.${step}`)}
                </button>
              </li>
            )
          })}
        </ol>
        {status === 'received' && (
          <form className="mt-3 flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); void saveStatus('received') }}>
            <label className="grid text-sm">{t('pack.amount')}
              <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="numeric" placeholder="₹"
                className="tap rounded-md border border-ink/30 bg-white px-3 text-base" />
            </label>
            <Button type="submit">{t('pack.save_amount')}</Button>
          </form>
        )}
        <p role="status" className="mt-2 min-h-5 text-sm text-soft">{note}</p>
      </section>
    </>
  )
}
