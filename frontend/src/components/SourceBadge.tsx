// Source + freshness: where the rule comes from, when we last checked it, and the scheme's status.
import { formatDate } from '../lib/format'
import { useStore } from '../lib/store'
import type { SchemeCardInfo } from '../lib/types'
import { Icon } from './ui'

export function SourceBadge({ scheme, stale, detailed = false }: { scheme: SchemeCardInfo; stale: boolean; detailed?: boolean }) {
  const { t, lang } = useStore()
  const date = formatDate(scheme.last_verified, lang)
  const badge =
    scheme.status === 'announced' ? { text: t('badge.announced'), cls: 'bg-muted text-muted-foreground', icon: 'clock' }
    : scheme.status === 'verify' ? { text: t('badge.verify'), cls: 'bg-warning-wash text-warning', icon: 'alert' }
    : stale ? { text: t('badge.stale'), cls: 'bg-warning-wash text-warning', icon: 'alert' }
    : { text: t('badge.verified', { date }), cls: 'bg-success-wash text-success', icon: 'check' }
  const source = scheme.sources[0]

  return (
    <div className="text-sm">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className={`inline-flex items-center gap-1 rounded-sm px-2 py-0.5 font-medium ${badge.cls}`}>
          <Icon name={badge.icon} className="h-3.5 w-3.5" />{badge.text}
        </span>
        {(scheme.status !== 'active' || stale) && <span className="text-muted-foreground">{t('badge.last_checked', { date })}</span>}
      </div>
      {detailed && scheme.status_note && <p className="mt-2 max-w-[70ch] text-muted-foreground">{scheme.status_note}</p>}
      <p className="mt-1.5 text-muted-foreground">
        {t('badge.source')}{' '}
        <a href={source.url} target="_blank" rel="noreferrer" className="link">
          {source.title}
        </a>
        {source.publisher ? ` (${source.publisher})` : ''}
      </p>
      {detailed && scheme.sources.slice(1).map((s) => (
        <p key={s.id} className="text-muted-foreground">
          <a href={s.url} target="_blank" rel="noreferrer" className="link">{s.title}</a>
          {s.publisher ? ` (${s.publisher})` : ''}
        </p>
      ))}
    </div>
  )
}
