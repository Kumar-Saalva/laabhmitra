// Screen 3: criteria checklist, Why? / Why not?, source, documents, official link.
import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { AffordabilityPanel } from '../components/Affordability'
import { Buckets } from '../components/SchemeCard'
import { SourceBadge } from '../components/SourceBadge'
import { CriterionMark, TierBadge } from '../components/TierBadge'
import { Button, EmptyState, ErrorState, Icon, Loading, NeedProfile, PageTitle } from '../components/ui'
import { api } from '../lib/api'
import { speechLocale } from '../lib/format'
import { hasBasics, useStore } from '../lib/store'
import type { Explanation } from '../lib/types'

type Kind = 'why' | 'why_not'

export default function SchemeDetail() {
  const { id = '' } = useParams()
  const [params] = useSearchParams()
  const { t, lang, profile, evaluation, error, retry } = useStore()
  const [kind, setKind] = useState<Kind | null>((params.get('ask') as Kind | null) ?? null)
  const [explanation, setExplanation] = useState<Explanation | null>(null)
  const [explainError, setExplainError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const profileJson = JSON.stringify(profile)
  useEffect(() => {
    if (!kind || !hasBasics(profile)) return
    let cancelled = false
    setBusy(true)
    setExplainError(null)
    api.explain(profile, id, lang, kind)
      .then((e) => { if (!cancelled) setExplanation(e) })
      .catch((e: Error) => { if (!cancelled) setExplainError(e.message) })
      .finally(() => { if (!cancelled) setBusy(false) })
    return () => { cancelled = true }
  }, [kind, id, lang, profileJson])

  if (!hasBasics(profile)) return <NeedProfile />
  if (error) return <ErrorState message={error} onRetry={retry} />
  if (!evaluation) return <Loading />
  const result = evaluation.results.find((r) => r.scheme_id === id)
  if (!result) return <EmptyState title={t('detail.not_found')}><Link to="/results" className="link">{t('nav.results')}</Link></EmptyState>

  const { scheme } = result
  const criteria = result.criteria.filter((c) => c.result !== 'N/A')

  const speak = () => {
    if (!explanation || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(explanation.text.replace(/[✓✗?]/g, ''))
    utterance.lang = speechLocale(lang)
    window.speechSynthesis.speak(utterance)
  }

  return (
    <>
      <PageTitle title={scheme.short_name} back="/results" />
      <p className="-mt-3 text-muted-foreground">{scheme.name}{scheme.ministry ? `, ${scheme.ministry}` : ''}</p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <TierBadge tier={result.tier} />
        <span className="text-muted-foreground">{t('card.criteria', { met: result.met, total: result.total, unknown: result.unknown })}</span>
      </div>
      <p className="mt-4 max-w-[68ch] text-lg">{scheme.summary_plain}</p>
      {!result.visible && <p className="mt-3 notice p-3 text-sm">{t('detail.hidden')}</p>}
      {scheme.warning && <p className="mt-3 notice notice-success p-3 text-sm">{t('fraud.udyam_free')}</p>}
      {scheme.conflict_note && (
        <p className="mt-3 flex items-start gap-2 notice notice-warning p-3 text-sm">
          <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <span>{scheme.conflict_note} <Link to="/path" className="link font-semibold">{t('results.see_path')}</Link></span>
        </p>
      )}

      <section className="card mt-6 px-5 py-5 sm:px-8 sm:py-7">
        <h2 className="text-xl">{t('detail.money')}</h2>
        <Buckets result={result} />
        {result.estimate.how && ['ready', 'likely', 'one_step'].includes(result.tier) && (
          <p className="mt-2 text-sm text-muted-foreground">{t('detail.how')}: {result.estimate.how} {t('map.label')}</p>
        )}
      </section>

      {result.affordability && ['ready', 'likely', 'one_step'].includes(result.tier) && (
        <AffordabilityPanel key={scheme.id} initial={result.affordability} />
      )}

      <section className="card mt-6 px-5 py-5 sm:px-8 sm:py-7">
        <h2 className="text-xl">{t('detail.rules')}</h2>
        <ul className="mt-2 divide-y divide-border/70">
          {criteria.map((c) => (
            <li key={c.id} className="flex gap-3 py-2.5">
              <CriterionMark state={c.result} />
              <div>
                <p className="font-medium">{c.label}</p>
                {c.result === 'UNKNOWN' && <p className="text-sm text-warning">{t('detail.need_info')}</p>}
                {c.note && <p className="text-sm text-muted-foreground">{c.note}</p>}
                {c.result === 'FALSE' && c.fix && <p className="mt-0.5 text-sm text-info"><span className="font-semibold">{t('detail.fix')}:</span> {c.fix.label}</p>}
              </div>
            </li>
          ))}
        </ul>
        {result.unknown > 0 && <Link to="/" className="tap link mt-1 inline-flex items-center font-semibold">{t('detail.answer_more')}</Link>}

        <div className="mt-3 flex flex-wrap gap-2 border-t border-border pt-4">
          <Button variant={kind === 'why' ? 'primary' : 'quiet'} aria-pressed={kind === 'why'} onClick={() => setKind('why')}>{t('card.why')}</Button>
          <Button variant={kind === 'why_not' ? 'primary' : 'quiet'} aria-pressed={kind === 'why_not'} onClick={() => setKind('why_not')}>{t('card.why_not')}</Button>
        </div>
        <div aria-live="polite">
          {busy && <Loading label={t('detail.explaining')} />}
          {explainError && <ErrorState message={explainError} />}
          {!busy && explanation && kind && (
            <div className="mt-3 bg-muted p-4">
              <p className="whitespace-pre-line">{explanation.text}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                {'speechSynthesis' in window && <Button onClick={speak}><Icon name="sound" className="h-4 w-4" />{t('detail.listen')}</Button>}
                <span>{t('detail.rules_decide')}</span>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="card mt-6 px-5 py-5 sm:px-8 sm:py-7">
        <h2 className="text-xl">{t('detail.source')}</h2>
        <div className="mt-2"><SourceBadge scheme={scheme} stale={result.stale} detailed /></div>
      </section>

      <section className="card mt-6 px-5 py-5 sm:px-8 sm:py-7">
        <h2 className="text-xl">{t('detail.apply')}</h2>
        {scheme.application.channel && <p className="mt-1">{scheme.application.channel}</p>}
        {scheme.application.steps.length > 0 && (
          <ol className="mt-2 list-decimal space-y-1 pl-5">{scheme.application.steps.map((s) => <li key={s}>{s}</li>)}</ol>
        )}
        {scheme.documents.length > 0 && (
          <>
            <h3 className="mt-4 text-lg">{t('detail.documents')}</h3>
            <ul className="mt-1 list-disc space-y-0.5 pl-5">{scheme.documents.map((d) => <li key={d}>{d}</li>)}</ul>
          </>
        )}
        <div className="mt-4 flex flex-wrap gap-2">
          {scheme.status !== 'announced' && (
            <Link to={`/pack/${scheme.id}`} className="btn btn-primary">{t('detail.prepare')}</Link>
          )}
          {scheme.application.url && (
            <a href={scheme.application.url} target="_blank" rel="noreferrer" className="btn btn-outline">
              <Icon name="link" className="h-4 w-4" />{t('card.official')}
            </a>
          )}
        </div>
      </section>
    </>
  )
}
