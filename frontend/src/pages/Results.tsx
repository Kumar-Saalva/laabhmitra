// Screen 2: headline money entry, tabs by readiness tier, scheme cards, and the opportunity map.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Headline, OpportunityMap } from '../components/OpportunityMap'
import { SchemeCard } from '../components/SchemeCard'
import { TIERS, TIER_STYLE } from '../components/TierBadge'
import { EmptyState, ErrorState, Icon, Loading, NeedProfile, PageTitle, SectionLabel } from '../components/ui'
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
        <p className="mt-4 flex items-start gap-2 notice notice-info p-3">
          <Icon name="step" className="mt-1 h-4 w-4 shrink-0 text-info" />
          <span>
            {t('results.hint', { step: topStep.label, count: topStep.unlocks.length })}{' '}
            <Link to="/path" className="link font-semibold">{t('results.see_path')}</Link>
          </span>
        </p>
      )}

      <div role="tablist" aria-label={t('results.tabs')} className="mt-10 flex gap-1 overflow-x-auto border-b border-border">
        {TIERS.map((tier) => (
          <button key={tier} role="tab" type="button" aria-selected={active === tier} onClick={() => setTab(tier)}
            className={`tap flex shrink-0 items-center gap-1.5 border-b-2 px-3 ${active === tier ? `border-current font-semibold ${TIER_STYLE[tier].text}` : 'border-transparent text-muted-foreground hover:text-foreground'}`}>
            <Icon name={TIER_STYLE[tier].icon} className="h-4 w-4" />
            {t(`tier.${tier}`)} <span className="figure">{count(tier)}</span>
          </button>
        ))}
      </div>

      <div role="tabpanel" className="card rounded-t-none border-t-0 px-5 sm:px-8">
        {shown.length === 0
          ? <div className="py-6"><EmptyState title={t(`results.empty.${active}`)} /></div>
          : shown.map((result) => <SchemeCard key={result.scheme_id} result={result} />)}
      </div>

      <div className="mt-16"><SectionLabel>{t('map.title')}</SectionLabel></div>
      <h2 className="text-center text-[1.75rem] sm:text-[2.25rem]">{t('map.title')}</h2>
      <p className="mx-auto mb-6 mt-2 max-w-[62ch] text-center text-muted-foreground">{t('map.lead')}</p>
      <OpportunityMap map={map} />
    </div>
  )
}
