// Screen 2: headline money entry, tabs by readiness tier, scheme cards, and the opportunity map.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Headline, OpportunityMap } from '../components/OpportunityMap'
import { SchemeCard } from '../components/SchemeCard'
import { TIERS, TIER_STYLE } from '../components/TierBadge'
import { EmptyState, ErrorState, Icon, Loading, NeedProfile, PageTitle } from '../components/ui'
import { hasBasics, useStore } from '../lib/store'
import type { Tier } from '../lib/types'

export default function Results() {
  const { t, profile, evaluation, loading, error, retry } = useStore()
  const [tab, setTab] = useState<Tier | null>(null)

  const visible = evaluation?.results.filter((r) => r.visible) ?? []
  const count = (tier: Tier) => visible.filter((r) => r.tier === tier).length
  const firstWithResults = TIERS.find((tier) => count(tier) > 0) ?? 'ready'
  const active = tab ?? firstWithResults
  useEffect(() => { setTab(null) }, [JSON.stringify(profile)])

  if (!hasBasics(profile)) return <NeedProfile />
  if (error) return <ErrorState message={error} onRetry={retry} />
  if (!evaluation) return <Loading />

  const map = evaluation.opportunity_map
  const shown = visible.filter((r) => r.tier === active)
  const topStep = map.fix_plan[0]

  return (
    <div className={loading ? 'opacity-60' : ''}>
      <PageTitle title={t('results.title')} lead={t('results.lead')} />
      <Headline map={map} />

      {topStep && (
        <p className="mt-4 flex items-start gap-2 border-l-4 border-step bg-step-wash p-3">
          <Icon name="step" className="mt-1 h-4 w-4 shrink-0 text-step" />
          <span>
            {t('results.hint', { step: topStep.label, count: topStep.unlocks.length })}{' '}
            <Link to="/path" className="font-semibold underline underline-offset-2">{t('results.see_path')}</Link>
          </span>
        </p>
      )}

      <div role="tablist" aria-label={t('results.tabs')} className="mt-7 flex gap-1 overflow-x-auto border-b border-rule">
        {TIERS.map((tier) => (
          <button key={tier} role="tab" type="button" aria-selected={active === tier} onClick={() => setTab(tier)}
            className={`tap flex shrink-0 items-center gap-1.5 border-b-[3px] px-3 ${active === tier ? `border-current font-semibold ${TIER_STYLE[tier].text}` : 'border-transparent text-soft hover:text-ink'}`}>
            <Icon name={TIER_STYLE[tier].icon} className="h-4 w-4" />
            {t(`tier.${tier}`)} <span className="figure">{count(tier)}</span>
          </button>
        ))}
      </div>

      <div role="tabpanel" className="ledger border-t-0 px-5">
        {shown.length === 0
          ? <div className="py-6"><EmptyState title={t(`results.empty.${active}`)} /></div>
          : shown.map((result) => <SchemeCard key={result.scheme_id} result={result} />)}
      </div>

      <h2 className="mt-9 text-2xl">{t('map.title')}</h2>
      <p className="mb-3 max-w-[62ch] text-soft">{t('map.lead')}</p>
      <OpportunityMap map={map} />
    </div>
  )
}
