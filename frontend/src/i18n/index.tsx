// Tiny i18n: flat JSON files per language, {name} placeholders, English as the fallback.
import en from './en.json'
import hi from './hi.json'
import kn from './kn.json'
import type { Lang } from '../lib/types'

const STRINGS: Record<Lang, Record<string, string>> = { en, kn, hi }

export const LANGUAGES: { code: Lang; name: string }[] = [
  { code: 'en', name: 'English' },
  { code: 'kn', name: 'ಕನ್ನಡ' },
  { code: 'hi', name: 'हिन्दी' },
]

export type Translate = (key: string, vars?: Record<string, string | number>) => string

export function makeT(lang: Lang): Translate {
  return (key, vars) => {
    let text = STRINGS[lang][key] ?? STRINGS.en[key] ?? key
    for (const [name, value] of Object.entries(vars ?? {})) text = text.split(`{${name}}`).join(String(value))
    return text
  }
}

// For option values such as trade ids: use the translation if there is one, else a readable id.
export function optionLabel(t: Translate, value: string): string {
  const key = `opt.${value}`
  const text = t(key)
  return text === key ? value.replace(/_/g, ' ') : text
}
