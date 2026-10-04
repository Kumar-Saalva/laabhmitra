// Source + freshness: where the rule comes from, when we last checked it, and the scheme's status.
import { formatDate } from '../lib/format'
import { useStore } from '../lib/store'
import type { SchemeCardInfo } from '../lib/types'
import { Icon } from './ui'

export function SourceBadge({ scheme, stale, detailed = false }: { scheme: SchemeCardInfo; stale: boolean; detailed?: boolean }) {
  const { t, lang } = useStore()
  const date = formatDate(scheme.last_verified, lang)
  const badge =
    scheme.status === 'announced' ? { text: t('badge.announced'), cls: 'bg-slate-wash text-soft', icon: 'clock' }
    : scheme.status === 'verify' ? { text: t('badge.verify'), cls: 'bg-turmeric-wash text-turmeric', icon: 'alert' }
    : stale ? { text: t('badge.stale'), cls: 'bg-turmeric-wash text-turmeric', icon: 'alert' }
    : { text: t('badge.verified', { date }), cls: 'bg-leaf-wash text-leaf', icon: 'check' }
  const source = scheme.sources[0]

  return (
    <div className="text-sm">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className={`inline-flex items-center gap-1 rounded-sm px-2 py-0.5 font-medium ${badge.cls}`}>
          <Icon name={badge.icon} className="h-3.5 w-3.5" />{badge.text}
        </span>
        {(scheme.status !== 'active' || stale) && <span className="text-soft">{t('badge.last_checked', { date })}</span>}
      </div>
      {detailed && scheme.status_note && <p className="mt-2 max-w-[70ch] text-soft">{scheme.status_note}</p>}
      <p className="mt-1.5 text-soft">
        {t('badge.source')}{' '}
        <a href={source.url} target="_blank" rel="noreferrer" className="underline decoration-rule underline-offset-2 hover:text-ink">
          {source.title}
        </a>
        {source.publisher ? ` (${source.publisher})` : ''}
      </p>
      {detailed && scheme.sources.slice(1).map((s) => (
        <p key={s.id} className="text-soft">
          <a href={s.url} target="_blank" rel="noreferrer" className="underline decoration-rule underline-offset-2 hover:text-ink">{s.title}</a>
          {s.publisher ? ` (${s.publisher})` : ''}
        </p>
      ))}
    </div>
  )
}
