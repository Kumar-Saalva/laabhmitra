// Loan affordability: a warning badge and an estimated EMI. It never changes eligibility.
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { formatINR } from '../lib/format'
import { useStore } from '../lib/store'
import type { Affordability, BandKey } from '../lib/types'
import { Icon } from './ui'

const BAND_STYLE: Record<BandKey, { cls: string; icon: string }> = {
  comfortable: { cls: 'text-success bg-success-wash', icon: 'check' },
  tight: { cls: 'text-warning bg-warning-wash', icon: 'alert' },
  thin: { cls: 'text-warning bg-warning-wash', icon: 'alert' },
  strain: { cls: 'text-danger bg-danger-wash', icon: 'alert' },
  cannot_cover: { cls: 'text-danger bg-danger-wash', icon: 'alert' },
  unknown: { cls: 'text-muted-foreground bg-muted', icon: 'question' },
  no_fixed_emi: { cls: 'text-muted-foreground bg-muted', icon: 'question' },
}

const percent = (rate: number) => String(Math.round(rate * 1000) / 10)

export function AffordabilityBadge({ a }: { a: Affordability }) {
  const { t } = useStore()
  const style = BAND_STYLE[a.band_key]
  return (
    <span className={`inline-flex items-center gap-1 rounded-sm px-2 py-0.5 text-sm font-semibold ${style.cls}`}>
      <Icon name={style.icon} className="h-3.5 w-3.5" />
      {t('afford.badge', { band: t(`afford.band.${a.band_key}`) })}
    </span>
  )
}

// Badge + the EMI sentence + what is missing, if anything.
export function AffordabilityLine({ a }: { a: Affordability }) {
  const { t } = useStore()
  return (
    <div className="text-sm">
      <AffordabilityBadge a={a} />
      {a.band_key === 'no_fixed_emi' ? (
        <p className="mt-1 text-muted-foreground">{t('afford.no_fixed')}</p>
      ) : (
        <p className="mt-1">
          {t('afford.line', { emi: formatINR(a.emi ?? 0), rate: percent(a.annual_rate), months: a.tenure_months })}
        </p>
      )}
      {a.band_key === 'unknown' && a.basis === 'current_cash' && (
        <p className="text-muted-foreground">{t('afford.missing_cash')} <Link to="/" className="link">{t('nav.profile')}</Link></p>
      )}
      {a.band_key === 'unknown' && a.basis === 'project_report' && (
        <p className="text-muted-foreground">{t('afford.needs_report')} <Link to="/project" className="link">{t('nav.project')}</Link></p>
      )}
    </div>
  )
}

// Scheme detail: the same check with sliders for rate and tenure.
export function AffordabilityPanel({ initial }: { initial: Affordability }) {
  const { t, profile } = useStore()
  const [a, setA] = useState(initial)
  const [rate, setRate] = useState(Math.round(initial.annual_rate * 1000) / 10)
  const [months, setMonths] = useState(initial.tenure_months)
  const [failed, setFailed] = useState(false)
  const touched = useRef(false)

  // The profile changed elsewhere (new answers): start again from the engine's result.
  useEffect(() => { if (!touched.current) setA(initial) }, [initial])

  useEffect(() => {
    if (!touched.current) return
    const timer = setTimeout(() => {
      api.affordability(profile, initial.scheme_id, rate / 100, months)
        .then((result) => { setA(result); setFailed(false) })
        .catch(() => setFailed(true))
    }, 200)
    return () => clearTimeout(timer)
  }, [rate, months])

  const fixed = a.band_key !== 'no_fixed_emi'
  return (
    <section className="card mt-6 px-5 py-5 sm:px-8 sm:py-7">
      <h2 className="text-xl">{t('afford.title')}</h2>
      <p className="text-sm text-muted-foreground">{t('afford.lead')}</p>
      <div className="mt-3"><AffordabilityLine a={a} /></div>

      {fixed && (
        <>
          <dl className="mt-3 grid gap-x-4 gap-y-1 text-sm sm:grid-cols-[14rem_1fr]">
            <dt className="text-muted-foreground">{t('afford.principal')}</dt>
            <dd className="figure">{formatINR(a.principal)}</dd>
            {a.basis === 'current_cash' && a.monthly_surplus !== null && (
              <>
                <dt className="text-muted-foreground">{t('afford.surplus')}</dt>
                <dd className="figure">{formatINR(a.monthly_surplus)}</dd>
              </>
            )}
            {a.ratio !== null && (
              <>
                <dt className="text-muted-foreground">{t('afford.ratio')}</dt>
                <dd className="figure">{Math.round(a.ratio * 100)}%</dd>
              </>
            )}
            {a.dscr !== null && (
              <>
                <dt className="text-muted-foreground">{t('afford.dscr')}</dt>
                <dd className="figure">{a.dscr}</dd>
              </>
            )}
          </dl>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="grid gap-1 text-sm">
              <span>{t('afford.rate')}: <span className="figure">{rate}%</span></span>
              <input type="range" min={4} max={24} step={0.5} value={rate} className="tap w-full accent-accent-strong"
                onChange={(e) => { touched.current = true; setRate(Number(e.target.value)) }} />
            </label>
            <label className="grid gap-1 text-sm">
              <span>{t('afford.tenure')}: <span className="figure">{t('afford.months', { months })}</span></span>
              <input type="range" min={6} max={84} step={6} value={months} className="tap w-full accent-accent-strong"
                onChange={(e) => { touched.current = true; setMonths(Number(e.target.value)) }} />
            </label>
          </div>
        </>
      )}
      {failed && <p role="alert" className="mt-2 text-sm text-danger">{t('afford.failed')}</p>}
      <p className="mt-3 text-sm text-muted-foreground">{t('afford.note')}{a.scheme_id === 'pmegp' ? ' ' + t('afford.pmegp_note') : ''}</p>
    </section>
  )
}
