// Readiness tier shown like a passbook stamp. Always an icon plus words, never a percentage.
import { useStore } from '../lib/store'
import type { CriterionState, Tier } from '../lib/types'
import { Icon } from './ui'

export const TIERS: Exclude<Tier, 'hidden'>[] = ['ready', 'likely', 'one_step', 'not_now', 'watchlist']

export const TIER_STYLE: Record<Tier, { icon: string; text: string; wash: string }> = {
  ready: { icon: 'check', text: 'text-leaf', wash: 'bg-leaf-wash' },
  likely: { icon: 'question', text: 'text-turmeric', wash: 'bg-turmeric-wash' },
  one_step: { icon: 'step', text: 'text-step', wash: 'bg-step-wash' },
  not_now: { icon: 'cross', text: 'text-sindoor', wash: 'bg-sindoor-wash' },
  watchlist: { icon: 'clock', text: 'text-soft', wash: 'bg-slate-wash' },
  hidden: { icon: 'cross', text: 'text-soft', wash: 'bg-slate-wash' },
}

export function TierBadge({ tier }: { tier: Tier }) {
  const { t } = useStore()
  const style = TIER_STYLE[tier]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-sm border-[1.5px] border-current px-2 py-0.5 text-sm font-semibold ${style.text} ${style.wash}`}>
      <Icon name={style.icon} className="h-4 w-4" />
      {t(`tier.${tier}`)}
    </span>
  )
}

const MARK: Record<CriterionState, { icon: string; cls: string }> = {
  TRUE: { icon: 'check', cls: 'text-leaf bg-leaf-wash' },
  FALSE: { icon: 'cross', cls: 'text-sindoor bg-sindoor-wash' },
  UNKNOWN: { icon: 'question', cls: 'text-turmeric bg-turmeric-wash' },
  'N/A': { icon: 'cross', cls: 'text-soft bg-slate-wash' },
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
