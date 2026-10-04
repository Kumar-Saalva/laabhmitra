// One scheme as a card entry: tier, criteria count, money buckets (kept apart), source, actions.
import { Link } from 'react-router-dom'
import { formatINR, formatRange } from '../lib/format'
import { useStore } from '../lib/store'
import type { SchemeResult } from '../lib/types'
import { AffordabilityLine } from './Affordability'
import { SourceBadge } from './SourceBadge'
import { TierBadge } from './TierBadge'
import { Icon } from './ui'

// Amounts are only shown where the scheme is still open to the merchant.
const SHOW_MONEY = ['ready', 'likely', 'one_step']

export function Buckets({ result }: { result: SchemeResult }) {
  const { t } = useStore()
  const { estimate, scheme } = result
  const open = SHOW_MONEY.includes(result.tier)
  const fee = scheme.benefits.find((b) => b.type === 'fee_subsidy')
  const nonMoney = scheme.benefits.find((b) => b.type === 'non_monetary')
  const rows: { label: string; value: string; figure?: boolean }[] = []
  if (open && estimate.grant_max > 0) rows.push({ label: t('bucket.grant'), value: formatRange(estimate.grant_min, estimate.grant_max), figure: true })
  if (open && estimate.credit > 0) {
    const tier = estimate.tier_name ? ` (${estimate.tier_name})` : ''
    rows.push({ label: t(scheme.kind === 'credit_guarantee' ? 'bucket.guarantee' : 'bucket.credit'), value: t('money.up_to', { amount: formatINR(estimate.credit) }) + tier, figure: true })
  }
  if (fee) rows.push({ label: t('bucket.fee'), value: fee.label })
  if (nonMoney) rows.push({ label: t('bucket.non_monetary'), value: nonMoney.label })
  if (!rows.length) {
    const first = scheme.benefits[0]
    if (first) rows.push({ label: t(first.type === 'grant' ? 'bucket.grant' : 'bucket.credit'), value: first.label })
  }
  return (
    <dl className="mt-3 grid gap-x-4 gap-y-1 sm:grid-cols-[11rem_1fr]">
      {rows.map((row) => (
        <div key={row.label} className="contents">
          <dt className="text-sm text-muted-foreground sm:pt-0.5">{row.label}</dt>
          <dd className={row.figure ? 'figure' : ''}>{row.value}</dd>
        </div>
      ))}
    </dl>
  )
}

export function SchemeCard({ result }: { result: SchemeResult }) {
  const { t } = useStore()
  const { scheme } = result
  const blocked = result.tier === 'not_now' || result.tier === 'one_step'
  return (
    <article className="border-b border-border py-7 last:border-b-0">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-xl">
          <Link to={`/scheme/${scheme.id}`} className="decoration-accent underline-offset-4 hover:underline">{scheme.short_name}</Link>
        </h3>
        <TierBadge tier={result.tier} />
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        {t('card.criteria', { met: result.met, total: result.total, unknown: result.unknown })}
      </p>
      <p className="mt-2 max-w-[68ch]">{scheme.summary_plain}</p>
      <Buckets result={result} />
      {result.affordability && SHOW_MONEY.includes(result.tier) && (
        <div className="mt-3"><AffordabilityLine a={result.affordability} /></div>
      )}
      <div className="mt-3"><SourceBadge scheme={scheme} stale={result.stale} /></div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to={`/scheme/${scheme.id}?ask=${blocked ? 'why_not' : 'why'}`}
          className="btn btn-primary">
          {t(blocked ? 'card.why_not' : 'card.why')}
        </Link>
        {scheme.application.url && (
          <a href={scheme.application.url} target="_blank" rel="noreferrer"
            className="btn btn-outline">
            <Icon name="link" className="h-4 w-4" />{t('card.official')}
          </a>
        )}
      </div>
    </article>
  )
}
