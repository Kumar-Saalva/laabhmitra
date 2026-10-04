// The honest money view. Subsidies and credit sit in separate passbook columns and are never added.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatINR, formatRange } from '../lib/format'
import { useStore } from '../lib/store'
import type { BucketItem, OpportunityMap as Map } from '../lib/types'
import { Icon } from './ui'

// The headline entry at the top of Results.
export function Headline({ map }: { map: Map }) {
  const { t } = useStore()
  const h = map.headline
  return (
    <section aria-label={t('map.title')} className="ledger grid sm:grid-cols-2">
      <div className="p-5">
        <p className="text-soft">{t('headline.subsidy_label')}</p>
        {h.grant_max > 0 ? (
          <p className="figure mt-1 text-[2.1rem] leading-tight text-leaf sm:text-[2.6rem]">
            {t('money.up_to', { amount: formatINR(h.grant_max) })}
          </p>
        ) : (
          <p className="mt-1 text-xl font-semibold">{t('headline.no_subsidy')}</p>
        )}
        <p className="mt-1 text-sm text-soft">
          {h.grant_max > 0
            ? (h.grant_min !== h.grant_max ? t('headline.subsidy_range', { min: formatINR(h.grant_min) }) : t('headline.subsidy_note'))
            : t('headline.no_subsidy_note')}
        </p>
      </div>
      <div className="border-t border-rule p-5 sm:border-l sm:border-t-0">
        <p className="text-soft">{t('headline.credit_label')}</p>
        <p className="figure mt-1 text-[2.1rem] leading-tight sm:text-[2.6rem]">
          {t(h.credit_options === 1 ? 'headline.credit_one' : 'headline.credit_count', { count: h.credit_options })}
        </p>
        <p className="mt-1 text-sm text-soft">
          {h.credit_options > 0 ? t('headline.credit_note', { amount: formatINR(h.credit_largest) }) : t('headline.no_credit_note')}
        </p>
      </div>
      <p className="border-t border-rule bg-paper/60 px-5 py-2 text-sm text-soft sm:col-span-2">{t('headline.never_added')}</p>
    </section>
  )
}

function Bucket({ title, note, items, value }: { title: string; note: string; items: BucketItem[]; value: (i: BucketItem) => string }) {
  const { t } = useStore()
  return (
    <section className="border-t border-rule py-4 first:border-t-0">
      <h3 className="text-lg">{title}</h3>
      <p className="text-sm text-soft">{note}</p>
      {items.length === 0 ? (
        <p className="mt-2 text-soft">{t('map.none')}</p>
      ) : (
        <ul className="mt-2 divide-y divide-rule/70">
          {items.map((item) => (
            <li key={item.scheme_id + (item.label ?? '')} className="grid gap-x-4 py-2 sm:grid-cols-[12rem_1fr]">
              <Link to={`/scheme/${item.scheme_id}`} className="font-semibold underline decoration-rule underline-offset-2 hover:decoration-ink">
                {item.short_name}
              </Link>
              <span>
                <span className={item.label ? '' : 'figure'}>{value(item)}</span>
                <span className="ml-2 text-sm text-soft">{t(`tier.${item.tier}`)}{item.scheme_status === 'verify' ? `, ${t('badge.verify').toLowerCase()}` : ''}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export function OpportunityMap({ map }: { map: Map }) {
  const { t } = useStore()
  const [open, setOpen] = useState(false)
  const { buckets } = map
  const withHow = [...buckets.grants, ...buckets.credit].filter((i) => i.how)
  return (
    <div className="ledger px-5">
      <Bucket title={t('map.grants')} note={t('map.grants_note')} items={buckets.grants}
        value={(i) => formatRange(i.grant_min ?? 0, i.grant_max ?? 0)} />
      <Bucket title={t('map.credit')} note={t('map.credit_note')} items={buckets.credit}
        value={(i) => t('money.up_to', { amount: formatINR(i.credit ?? 0) }) + (i.tier_name ? ` (${i.tier_name})` : '')} />
      <Bucket title={t('map.fee')} note={t('map.fee_note')} items={buckets.fee_savings} value={(i) => i.label ?? ''} />
      <Bucket title={t('map.non_monetary')} note={t('map.non_monetary_note')} items={buckets.non_monetary} value={(i) => i.label ?? ''} />

      <div className="border-t border-rule py-4">
        <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
          className="tap flex w-full items-center justify-between text-left font-semibold">
          {t('map.how')}
          <Icon name="back" className={`h-4 w-4 transition-transform ${open ? 'rotate-90' : '-rotate-90'}`} />
        </button>
        {open && (
          <div className="pb-2 text-sm">
            <p className="max-w-[70ch] text-soft">{t('map.how_intro')}</p>
            <ul className="mt-2 space-y-1.5">
              {withHow.map((i) => (
                <li key={i.scheme_id + (i.credit ?? 'g')}><span className="font-semibold">{i.short_name}:</span> {i.how}</li>
              ))}
            </ul>
          </div>
        )}
        <p className="mt-2 text-sm text-soft">{t('map.label')}</p>
      </div>
    </div>
  )
}
