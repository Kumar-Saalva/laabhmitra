// Hidden route /admin: paste or edit a scheme JSON, validate it, run the three personas.
// English only on purpose: this screen is for the team, not for merchants.
import { useEffect, useState } from 'react'
import { Button, ErrorState, PageTitle } from '../components/ui'
import { api } from '../lib/api'
import { formatINR, formatRange } from '../lib/format'
import type { RuleTest } from '../lib/types'

export default function Admin() {
  const [schemes, setSchemes] = useState<{ id: string; short_name: string }[]>([])
  const [text, setText] = useState('')
  const [result, setResult] = useState<RuleTest | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => { api.schemes().then(setSchemes).catch((e: Error) => setError(e.message)) }, [])

  const loadScheme = async (id: string) => {
    if (!id) return
    setResult(null)
    setError(null)
    try {
      setText(JSON.stringify(await api.scheme(id), null, 2))
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const run = async () => {
    setError(null)
    setResult(null)
    let scheme: unknown
    try {
      scheme = JSON.parse(text)
    } catch (e) {
      setError(`This is not valid JSON: ${(e as Error).message}`)
      return
    }
    setBusy(true)
    try {
      setResult(await api.testScheme(scheme))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageTitle title="Rule tester" lead="Paste a scheme definition, or load one and edit it. Nothing is saved: to add a scheme for real, a person edits data/schemes.seed.json after checking the official source." />
      <div className="flex flex-wrap items-end gap-3">
        <label className="grid text-sm">Load an existing scheme
          <select onChange={(e) => loadScheme(e.target.value)} defaultValue="" className="tap rounded-md border border-ink/30 bg-white px-3 text-base">
            <option value="">Choose a scheme</option>
            {schemes.map((s) => <option key={s.id} value={s.id}>{s.short_name}</option>)}
          </select>
        </label>
        <Button variant="primary" onClick={run} disabled={busy || !text.trim()}>{busy ? 'Running' : 'Run persona tests'}</Button>
      </div>
      <label htmlFor="scheme-json" className="mt-4 block text-sm">Scheme JSON</label>
      <textarea id="scheme-json" value={text} onChange={(e) => setText(e.target.value)} spellCheck={false} rows={18}
        placeholder='{"id": "my_scheme", "short_name": "...", "kind": "credit", "status": "active", "criteria": [...], ...}'
        className="w-full rounded-md border border-ink/30 bg-white p-3 font-mono text-sm" />

      {error && <ErrorState message={error} />}
      {result && !result.valid && (
        <div role="alert" className="mt-4 border-l-4 border-sindoor bg-sindoor-wash p-4">
          <p className="font-semibold text-sindoor">The scheme is not valid yet. Fix these and run again:</p>
          <ul className="mt-1 list-disc pl-5 text-sm">{result.errors.map((e) => <li key={e}>{e}</li>)}</ul>
        </div>
      )}
      {result && result.warnings.length > 0 && (
        <div className="mt-4 border-l-4 border-turmeric bg-turmeric-wash p-4 text-sm">
          <ul className="list-disc pl-5">{result.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      )}
      {result?.valid && (
        <div className="ledger mt-4 overflow-x-auto p-4">
          <p className="mb-2 text-sm text-soft">{result.is_new ? 'New scheme: no expected results to compare against.' : 'Compared against data/expected.json.'}</p>
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead>
              <tr className="border-b border-rule">
                <th className="py-2 pr-3">Persona</th><th className="pr-3">Status</th><th className="pr-3">Met</th>
                <th className="pr-3">Fails</th><th className="pr-3">Grant</th><th className="pr-3">Credit</th><th>Expected</th>
              </tr>
            </thead>
            <tbody>
              {result.results.map((r) => (
                <tr key={r.persona} className="border-b border-rule/70 last:border-0">
                  <td className="py-2 pr-3 font-semibold">{r.display_name}</td>
                  <td className="pr-3">{r.status}</td>
                  <td className="figure pr-3">{r.met}/{r.total} ({r.unknown}?)</td>
                  <td className="pr-3">{r.fails.join(', ') || 'none'}</td>
                  <td className="figure pr-3">{r.grant_max ? formatRange(r.grant_min, r.grant_max) : 'none'}</td>
                  <td className="figure pr-3">{r.credit ? formatINR(r.credit) : 'none'}</td>
                  <td className={r.matches_expected === false ? 'font-semibold text-sindoor' : r.matches_expected ? 'text-leaf' : 'text-soft'}>
                    {r.matches_expected === null ? 'no baseline' : r.matches_expected ? 'matches' : `changed (was ${r.expected_status})`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
