// Screen 1: language, consent, then the profile chat with a live "Your business" card.
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LANGUAGES } from '../i18n'
import { ProfileChat, showValue } from '../components/ProfileChat'
import { Button, ErrorState, PageTitle } from '../components/ui'
import { api } from '../lib/api'
import { CARD_FIELDS } from '../lib/questions'
import { hasBasics, useStore } from '../lib/store'
import type { Profile } from '../lib/types'

type Personas = Record<string, Profile & { display_name: string; story: string }>

function Consent() {
  const { t, lang, setLang, giveConsent } = useStore()
  const [agreed, setAgreed] = useState(false)
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-[2.2rem] sm:text-[3rem]">{t('welcome.title')}</h1>
      <p className="mt-3 max-w-[58ch] text-lg text-soft">{t('welcome.lead')}</p>

      <fieldset className="mt-7">
        <legend className="font-semibold">{t('welcome.language')}</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {LANGUAGES.map((l) => (
            <button key={l.code} type="button" onClick={() => setLang(l.code)} aria-pressed={lang === l.code} lang={l.code}
              className={`tap rounded-md border px-5 text-lg ${lang === l.code ? 'border-ink bg-ink text-sheet' : 'border-ink/30 bg-sheet hover:border-ink'}`}>
              {l.name}
            </button>
          ))}
        </div>
      </fieldset>

      <section className="ledger mt-7 p-5">
        <h2 className="text-xl">{t('consent.title')}</h2>
        <ul className="mt-3 list-disc space-y-1.5 pl-5">
          <li>{t('consent.use')}</li>
          <li>{t('consent.no_ids')}</li>
          <li>{t('consent.optional')}</li>
          <li>{t('consent.no_submit')}</li>
        </ul>
        <label className="tap mt-4 flex cursor-pointer items-start gap-3">
          <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} className="mt-1 h-5 w-5 accent-ink" />
          <span>{t('consent.agree')}</span>
        </label>
        <Button variant="primary" className="mt-4 w-full sm:w-auto" disabled={!agreed} onClick={giveConsent}>{t('consent.start')}</Button>
      </section>
    </div>
  )
}

function BusinessCard() {
  const { t, profile } = useStore()
  const filled = CARD_FIELDS.filter((f) => profile[f] != null && profile[f] !== '')
  return (
    <section className="ledger p-5" aria-live="polite">
      <h2 className="text-xl">{t('business.title')}</h2>
      {filled.length === 0 ? (
        <p className="mt-2 text-soft">{t('business.empty')}</p>
      ) : (
        <dl className="mt-3 divide-y divide-rule/70">
          {filled.map((f) => (
            <div key={f} className="flex justify-between gap-4 py-1.5">
              <dt className="text-soft">{t(`field.${f}`)}</dt>
              <dd className={`text-right font-medium ${f.endsWith('_inr') ? 'figure' : ''}`}>{showValue(t, f, profile[f])}</dd>
            </div>
          ))}
        </dl>
      )}
      <p className="mt-3 text-sm text-soft">{t('business.privacy')}</p>
    </section>
  )
}

export default function Onboard() {
  const { t, consent, profile, error, retry, replaceProfile, save, reset } = useStore()
  const navigate = useNavigate()
  const [personas, setPersonas] = useState<Personas>({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => { api.personas().then(setPersonas).catch(() => setPersonas({})) }, [])

  if (!consent) return <Consent />

  const finish = async (toSave?: Profile, fresh = false) => {
    setSaving(true)
    setSaveError(null)
    try {
      await save(toSave, fresh)
      navigate('/results')
    } catch (e) {
      setSaveError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const loadPersona = (key: string) => {
    const { display_name: _name, story: _story, ...facts } = personas[key]
    replaceProfile(facts)
    void finish(facts, true)
  }

  return (
    <>
      <PageTitle title={t('onboard.title')} lead={t('onboard.lead')} />
      {error && <ErrorState message={error} onRetry={retry} />}
      {saveError && <ErrorState message={saveError} />}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div>
          <ProfileChat />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button variant="primary" disabled={!hasBasics(profile) || saving} onClick={() => finish()}>
              {saving ? t('state.saving') : t('onboard.see_results')}
            </Button>
            {!hasBasics(profile) && <span className="text-sm text-soft">{t('onboard.need_basics')}</span>}
            {Object.keys(profile).length > 0 && <Button onClick={reset}>{t('onboard.start_over')}</Button>}
          </div>
        </div>
        <div className="space-y-5">
          <BusinessCard />
          <section>
            <h2 className="text-lg">{t('demo.title')}</h2>
            <p className="text-sm text-soft">{t('demo.lead')}</p>
            <div className="mt-2 grid gap-2">
              {Object.entries(personas).map(([key, persona]) => (
                <button key={key} type="button" onClick={() => loadPersona(key)} disabled={saving}
                  className="tap rounded-md border border-ink/30 bg-sheet px-4 py-2 text-left hover:border-ink">
                  <span className="font-semibold">{persona.display_name}</span>
                  <span className="block text-sm text-soft">{persona.story}</span>
                </button>
              ))}
              {Object.keys(personas).length === 0 && <p className="text-sm text-soft">{t('demo.none')}</p>}
            </div>
          </section>
        </div>
      </div>
    </>
  )
}
