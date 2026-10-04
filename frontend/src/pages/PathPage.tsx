// Screen 4: best paths side by side, conflict warnings, credit options, unlock steps.
import { Link } from 'react-router-dom'
import { PathView, UnlockSteps } from '../components/PathView'
import { EmptyState, ErrorState, Loading, NeedProfile, PageTitle } from '../components/ui'
import { formatINR } from '../lib/format'
import { hasBasics, useStore } from '../lib/store'

export default function PathPage() {
  const { t, profile, evaluation, error, retry } = useStore()
  if (!hasBasics(profile)) return <NeedProfile />
  if (error) return <ErrorState message={error} onRetry={retry} />
  if (!evaluation) return <Loading />

  const map = evaluation.opportunity_map
  return (
    <>
      <PageTitle title={t('path.title')} lead={t('path.lead')} />
      {map.best_paths.length === 0
        ? <EmptyState title={t('path.none')}><p>{t('path.none_help')}</p></EmptyState>
        : <PathView evaluation={evaluation} />}

      <section className="card mt-6 p-5 sm:p-8">
        <h2 className="text-xl">{t('map.credit')}</h2>
        <p className="text-sm text-muted-foreground">{t('path.credit_note')}</p>
        {map.buckets.credit.length === 0 ? <p className="mt-2 text-muted-foreground">{t('map.none')}</p> : (
          <ul className="mt-2 divide-y divide-border/70">
            {map.buckets.credit.map((c) => (
              <li key={c.scheme_id} className="flex flex-wrap justify-between gap-x-4 py-2">
                <Link to={`/scheme/${c.scheme_id}`} className="font-semibold link">{c.short_name}</Link>
                <span>
                  <span className="figure">{t('money.up_to', { amount: formatINR(c.credit ?? 0) })}{c.tier_name ? ` (${c.tier_name})` : ''}</span>
                  <span className="ml-2 text-sm text-muted-foreground">{t(`tier.${c.tier}`)}{c.scheme_status === 'verify' ? `, ${t('badge.verify').toLowerCase()}` : ''}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="mt-5"><UnlockSteps steps={map.fix_plan} /></div>
      <p className="mt-4 text-sm text-muted-foreground">{t('map.label')}</p>
    </>
  )
}
