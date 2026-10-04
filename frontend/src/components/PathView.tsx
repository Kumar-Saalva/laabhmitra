// Benefit Path Planner: the best sets of subsidy schemes that can be combined, side by side.
import { Link } from 'react-router-dom'
import { formatINR, formatRange } from '../lib/format'
import { useStore } from '../lib/store'
import type { Evaluation, FixStep, Path } from '../lib/types'
import { TierBadge } from './TierBadge'
import { Icon } from './ui'

const LETTERS = ['A', 'B', 'C']

function PathColumn({ path, index, evaluation }: { path: Path; index: number; evaluation: Evaluation }) {
  const { t } = useStore()
  const results = path.schemes.map((id) => evaluation.results.find((r) => r.scheme_id === id)!)
  return (
    <section className={`card flex flex-col p-6 sm:p-8 ${index === 0 ? 'card-accent' : ''}`}>
      <h2 className="text-xl">{t('path.name', { letter: LETTERS[index] })}{index === 0 ? ` (${t('path.largest')})` : ''}</h2>
      <p className="display-figure mt-2 text-[2.1rem] text-success">{formatRange(path.grant_min, path.grant_max)}</p>
      <p className="text-sm text-muted-foreground">{t('path.subsidy_total')}</p>
      {/* A real sequence: the order to apply in. */}
      <ol className="mt-4 space-y-3">
        {results.map((r, n) => (
          <li key={r.scheme_id} className="grid grid-cols-[1.75rem_1fr] gap-x-2">
            <span className="figure flex h-7 w-7 items-center justify-center rounded-full bg-foreground text-sm text-card">{n + 1}</span>
            <div>
              <Link to={`/scheme/${r.scheme_id}`} className="font-semibold link">
                {r.scheme.short_name}
              </Link>{' '}
              <TierBadge tier={r.tier} />
              <p className="text-sm">
                {t('bucket.grant')}: <span className="figure">{formatRange(r.estimate.grant_min, r.estimate.grant_max)}</span>
                {r.estimate.credit > 0 && <> ; {t('path.plus_credit', { amount: formatINR(r.estimate.credit) })}</>}
              </p>
            </div>
          </li>
        ))}
      </ol>
      {path.conflicts.length > 0 && (
        <div className="mt-4 notice notice-warning p-3 text-sm">
          <p className="flex items-center gap-1.5 font-semibold text-warning"><Icon name="alert" className="h-4 w-4" />{t('path.tradeoff')}</p>
          {path.conflicts.map((message) => <p key={message} className="mt-1">{message}</p>)}
        </div>
      )}
    </section>
  )
}

export function UnlockSteps({ steps }: { steps: FixStep[] }) {
  const { t } = useStore()
  if (!steps.length) return null
  return (
    <section className="card p-6 sm:p-8">
      <h2 className="text-xl">{t('path.unlock_title')}</h2>
      <p className="text-sm text-muted-foreground">{t('path.unlock_lead')}</p>
      <ul className="mt-3 divide-y divide-border">
        {steps.map((step) => (
          <li key={step.action_id} className="py-3">
            <p className="flex items-start gap-2 font-semibold"><Icon name="step" className="mt-1 h-4 w-4 shrink-0 text-info" />{step.label}</p>
            <p className="ml-6">{t('path.unlocks', { count: step.unlocks.length, names: step.unlock_names.join(', ') })}</p>
            <p className="ml-6 text-sm text-muted-foreground">
              {step.grant_unlocked > 0 && <>{t('path.unlocks_grant', { amount: formatINR(step.grant_unlocked) })} </>}
              {step.credit_unlocked_max > 0 && t('path.unlocks_credit', { amount: formatINR(step.credit_unlocked_max) })}
            </p>
            {step.action_id === 'register_udyam' && <p className="ml-6 mt-1 text-sm text-success">{t('fraud.udyam_free')}</p>}
          </li>
        ))}
      </ul>
    </section>
  )
}

export function PathView({ evaluation }: { evaluation: Evaluation }) {
  const paths = evaluation.opportunity_map.best_paths
  return (
    <div className={`grid gap-6 ${paths.length > 1 ? 'lg:grid-cols-2' : ''}`}>
      {paths.map((path, index) => <PathColumn key={path.schemes.join('+')} path={path} index={index} evaluation={evaluation} />)}
    </div>
  )
}
