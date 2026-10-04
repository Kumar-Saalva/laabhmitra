// Readiness tier badge. Always an icon plus words, never a percentage.
import { useStore } from '../lib/store'
import type { CriterionState, Tier } from '../lib/types'
import { Icon } from './ui'

export const TIERS: Exclude<Tier, 'hidden'>[] = ['ready', 'likely', 'one_step', 'not_now', 'watchlist']

export const TIER_STYLE: Record<Tier, { icon: string; text: string; wash: string }> = {
  ready: { icon: 'check', text: 'text-success', wash: 'bg-success-wash' },
  likely: { icon: 'question', text: 'text-warning', wash: 'bg-warning-wash' },
  one_step: { icon: 'step', text: 'text-info', wash: 'bg-info-wash' },
  not_now: { icon: 'cross', text: 'text-danger', wash: 'bg-danger-wash' },
  watchlist: { icon: 'clock', text: 'text-muted-foreground', wash: 'bg-muted' },
  hidden: { icon: 'cross', text: 'text-muted-foreground', wash: 'bg-muted' },
}

export function TierBadge({ tier }: { tier: Tier }) {
  const { t } = useStore()
  const style = TIER_STYLE[tier]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border border-current/40 px-2 py-0.5 text-sm font-semibold ${style.text} ${style.wash}`}>
      <Icon name={style.icon} className="h-4 w-4" />
      {t(`tier.${tier}`)}
    </span>
  )
}

const MARK: Record<CriterionState, { icon: string; cls: string }> = {
  TRUE: { icon: 'check', cls: 'text-success bg-success-wash' },
  FALSE: { icon: 'cross', cls: 'text-danger bg-danger-wash' },
  UNKNOWN: { icon: 'question', cls: 'text-warning bg-warning-wash' },
  'N/A': { icon: 'cross', cls: 'text-muted-foreground bg-muted' },
}

export function CriterionMark({ state }: { state: CriterionState }) {
  const { t } = useStore()
  const mark = MARK[state]
  return (
    <span className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${mark.cls}`}>
      <Icon name={mark.icon} className="h-4 w-4" />
      <span className="sr-only">{t(`criterion.${state}`)}</span>
    </span>
  )
}
