// Project details form + project report draft (new units, PMEGP first).
// Every figure is computed by the backend engine; this page only collects inputs and shows tables.
import { useState, type FormEvent } from 'react'
import { AffordabilityBadge } from '../components/Affordability'
import { Button, ErrorState, Icon, NeedProfile, PageTitle } from '../components/ui'
import { api } from '../lib/api'
import { formatINR } from '../lib/format'
import { hasBasics, useStore } from '../lib/store'
import type { Affordability, ProjectDetails, ProjectReport } from '../lib/types'

const MONEY_FIELDS = ['machinery_inr', 'building_or_civil_inr', 'working_capital_inr', 'monthly_sales_year1_inr', 'monthly_fixed_costs_inr'] as const
const PERCENT_FIELDS = ['annual_sales_growth', 'raw_material_pct_of_sales'] as const
type NumberField = (typeof MONEY_FIELDS)[number] | (typeof PERCENT_FIELDS)[number]

// The form holds text; percentages are typed as 10 and stored as 0.10.
function toForm(project: ProjectDetails): Record<string, string> {
  const form: Record<string, string> = { business_description: project.business_description ?? '' }
  for (const f of MONEY_FIELDS) form[f] = project[f] != null ? String(project[f]) : ''
  for (const f of PERCENT_FIELDS) form[f] = project[f] != null ? String(Math.round((project[f] as number) * 1000) / 10) : ''
  return form
}

function toProject(form: Record<string, string>): ProjectDetails {
  const number = (text: string) => (text.trim() === '' || Number.isNaN(Number(text.replace(/,/g, ''))) ? null : Number(text.replace(/,/g, '')))
  const project: ProjectDetails = { business_description: form.business_description.trim() || null }
  for (const f of MONEY_FIELDS) { const n = number(form[f]); project[f] = n === null ? null : Math.round(n) }
  for (const f of PERCENT_FIELDS) { const n = number(form[f]); project[f] = n === null ? null : n / 100 }
  return project
}

function Row({ label, values, strong = false }: { label: string; values: (string | number)[]; strong?: boolean }) {
  return (
    <tr className={`border-b border-rule/70 last:border-0 ${strong ? 'font-semibold' : ''}`}>
      <th scope="row" className="py-1.5 pr-3 text-left font-normal">{strong ? <span className="font-semibold">{label}</span> : label}</th>
      {values.map((v, i) => <td key={i} className="figure py-1.5 pl-3 text-right">{v}</td>)}
    </tr>
  )
}

function Report({ report }: { report: ProjectReport }) {
  const { t } = useStore()
  const { cost_of_project: cost, means_of_finance: finance, loan, years } = report
  const head = (
    <thead>
      <tr className="border-b border-ink/40">
        <th />{years.map((y) => <th key={y.year} scope="col" className="py-1.5 pl-3 text-right">{t('project.year', { year: y.year })}</th>)}
      </tr>
    </thead>
  )
  const band = { band: report.band, band_key: report.band_key } as Affordability
  return (
    <div className="mt-6 space-y-5">
      <section className="ledger p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-xl">{t('project.report')}</h2>
          <span className="rounded-sm border-[1.5px] border-sindoor px-2 py-0.5 text-sm font-semibold text-sindoor">{t('project.draft')}</span>
        </div>
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          <div><p className="text-sm text-soft">{t('project.emi')}</p><p className="figure text-2xl">{formatINR(loan.emi)}</p></div>
          <div><p className="text-sm text-soft">{t('project.avg_dscr')}</p><p className="figure text-2xl">{report.average_dscr ?? '?'}</p></div>
          <div><p className="text-sm text-soft">{t('project.repayment')}</p><p className="mt-1"><AffordabilityBadge a={band} /></p></div>
        </div>
        <p className="mt-3 text-sm text-soft">{t('project.terms', { rate: Math.round(loan.annual_rate * 1000) / 10, months: loan.tenure_months })}</p>
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="ledger p-5">
          <h3 className="text-lg">{t('project.cost')}</h3>
          <table className="mt-2 w-full text-sm"><tbody>
            <Row label={t('project.f.machinery_inr')} values={[formatINR(cost.machinery)]} />
            <Row label={t('project.f.building_or_civil_inr')} values={[formatINR(cost.building_or_civil)]} />
            <Row label={t('project.f.working_capital_inr')} values={[formatINR(cost.working_capital)]} />
            <Row label={t('project.total')} values={[formatINR(cost.total)]} strong />
          </tbody></table>
        </section>
        <section className="ledger p-5">
          <h3 className="text-lg">{t('project.finance')}</h3>
          <table className="mt-2 w-full text-sm"><tbody>
            <Row label={t('project.own', { pct: Math.round(finance.own_contribution_rate * 100) })} values={[formatINR(finance.own_contribution)]} />
            <Row label={t('project.bank_loan')} values={[formatINR(finance.bank_loan)]} />
            <Row label={t('project.total')} values={[formatINR(cost.total)]} strong />
          </tbody></table>
          <p className="mt-3 border-t border-rule pt-2 text-sm">
            {t('project.subsidy')}: <span className="figure text-leaf">{formatINR(finance.subsidy_estimate)}</span>
          </p>
          <p className="text-sm text-soft">{t('project.subsidy_note')}</p>
        </section>
      </div>

      <section className="ledger overflow-x-auto p-5">
        <h3 className="text-lg">{t('project.projection')}</h3>
        <table className="mt-2 w-full min-w-[30rem] text-sm">{head}<tbody>
          <Row label={t('project.sales')} values={years.map((y) => formatINR(y.sales))} />
          <Row label={t('project.raw')} values={years.map((y) => formatINR(y.raw_material))} />
          <Row label={t('project.fixed')} values={years.map((y) => formatINR(y.fixed_costs))} />
          <Row label={t('project.depreciation')} values={years.map((y) => formatINR(y.depreciation))} />
          <Row label={t('project.interest')} values={years.map((y) => formatINR(y.interest))} />
          <Row label={t('project.pbt')} values={years.map((y) => formatINR(y.profit_before_tax))} strong />
        </tbody></table>
      </section>

      <section className="ledger overflow-x-auto p-5">
        <h3 className="text-lg">{t('project.dscr_title')}</h3>
        <table className="mt-2 w-full min-w-[30rem] text-sm">{head}<tbody>
          <Row label={t('project.cash_accrual')} values={years.map((y) => formatINR(y.cash_accrual))} />
          <Row label={t('project.interest')} values={years.map((y) => formatINR(y.interest))} />
          <Row label={t('project.principal')} values={years.map((y) => formatINR(y.principal_repaid))} />
          <Row label="DSCR" values={years.map((y) => y.dscr ?? '?')} strong />
        </tbody></table>
        <p className="mt-2 text-sm text-soft">{t('project.dscr_note')}</p>
      </section>

      <section className="ledger p-5">
        <h3 className="text-lg">{t('project.assumptions')}</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{report.assumptions.map((a) => <li key={a}>{a}</li>)}</ul>
      </section>

      <section className="ledger p-5">
        <h3 className="text-lg">{t('project.narrative')}</h3>
        <p className="text-sm text-soft">{t('project.narrative_note')}</p>
        {Object.entries(report.narrative.sections).map(([key, text]) => (
          <div key={key} className="mt-3">
            <h4 className="font-semibold">{report.narrative.titles[key]}</h4>
            <p className="max-w-[72ch]">{text}</p>
          </div>
        ))}
      </section>
    </div>
  )
}

export default function Project() {
  const { t, profile, update, save } = useStore()
  const [form, setForm] = useState(() => toForm((profile.project as ProjectDetails) ?? {}))
  const [report, setReport] = useState<ProjectReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState<string | null>(null)

  if (!hasBasics(profile)) return <NeedProfile />

  const set = (field: string, value: string) => setForm((f) => ({ ...f, [field]: value }))

  const calculate = async (changes: Record<string, unknown> = {}) => {
    setBusy(true)
    setError(null)
    setNote(null)
    try {
      const project = toProject(form)
      const next = { ...profile, ...changes, project }
      update({ ...changes, project })
      setReport(await api.projectReport(next))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const submit = (event: FormEvent) => { event.preventDefault(); void calculate() }

  const download = async () => {
    setBusy(true)
    setNote(null)
    try {
      const { profileId } = await save({ ...profile, project: toProject(form) })
      const url = URL.createObjectURL(await api.projectReportPdf(profileId))
      const link = document.createElement('a')
      link.href = url
      link.download = 'laabhmitra-project-report-draft.pdf'
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      setNote(t('pack.download_failed'))
    } finally {
      setBusy(false)
    }
  }

  const field = (name: NumberField, suffix: string) => (
    <label key={name} className="grid gap-1 text-sm">
      <span>{t(`project.f.${name}`)}</span>
      <span className="flex items-center gap-2">
        <input value={form[name]} onChange={(e) => set(name, e.target.value)} inputMode="decimal" autoComplete="off"
          className="tap min-w-0 flex-1 rounded-md border border-ink/30 bg-white px-3 text-base" />
        <span className="w-6 text-soft">{suffix}</span>
      </span>
      <span className="text-soft">{t(`project.h.${name}`)}</span>
    </label>
  )

  const mismatch = report?.complete ? report.cost_mismatch : null

  return (
    <>
      <PageTitle title={t('project.title')} lead={t('project.lead')} />
      {profile.is_new_project !== true && <p className="mb-4 border-l-4 border-turmeric bg-turmeric-wash p-3 text-sm">{t('project.only_new')}</p>}

      <form onSubmit={submit} className="ledger p-5">
        <h2 className="text-xl">{t('project.details')}</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          {field('machinery_inr', '₹')}
          {field('building_or_civil_inr', '₹')}
          {field('working_capital_inr', '₹')}
          {field('monthly_sales_year1_inr', '₹')}
          {field('monthly_fixed_costs_inr', '₹')}
          {field('raw_material_pct_of_sales', '%')}
          {field('annual_sales_growth', '%')}
        </div>
        <label className="mt-4 grid gap-1 text-sm">
          <span>{t('project.f.business_description')}</span>
          <textarea value={form.business_description} onChange={(e) => set('business_description', e.target.value)} rows={3} maxLength={2000}
            className="rounded-md border border-ink/30 bg-white p-3 text-base" />
          <span className="text-soft">{t('project.h.business_description')}</span>
        </label>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button type="submit" variant="primary" disabled={busy}>{busy ? t('state.loading') : t('project.calculate')}</Button>
          {report?.complete && <Button onClick={download} disabled={busy}><Icon name="download" className="h-4 w-4" />{t('project.download')}</Button>}
        </div>
        <p role="status" className="mt-2 min-h-5 text-sm text-sindoor">{note}</p>
      </form>

      {error && <ErrorState message={error} />}
      {report && !report.complete && (
        <div role="alert" className="mt-4 border-l-4 border-turmeric bg-turmeric-wash p-4">
          <p className="font-semibold">{t('project.missing')}</p>
          <ul className="mt-1 list-disc pl-5 text-sm">{report.missing?.map((f) => <li key={f}>{t(`project.f.${f}`)}</li>)}</ul>
        </div>
      )}
      {mismatch && (
        <div role="alert" className="mt-4 border-l-4 border-turmeric bg-turmeric-wash p-4">
          <p className="font-semibold">{t('project.mismatch_title')}</p>
          <p className="mt-1">{t('project.mismatch', { details: formatINR(mismatch.from_details), profile: formatINR(mismatch.from_profile) })}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button disabled={busy} onClick={() => calculate({ project_cost_inr: mismatch.from_details })}>{t('project.use_details', { amount: formatINR(mismatch.from_details) })}</Button>
            <span className="self-center text-sm text-soft">{t('project.or_fix')}</span>
          </div>
        </div>
      )}
      {report?.complete && <Report report={report} />}
    </>
  )
}
