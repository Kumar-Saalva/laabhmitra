import type { Lang } from './types'

// The single rupee formatter for the whole app: 280000 -> ₹2,80,000 (Indian grouping).
export function formatINR(amount: number): string {
  return '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Math.round(amount))
}

export function formatRange(min: number, max: number): string {
  return min === max ? formatINR(max) : `${formatINR(min)} – ${formatINR(max)}`
}

const LOCALES: Record<Lang, string> = { en: 'en-IN', kn: 'kn-IN', hi: 'hi-IN' }

export function formatDate(iso: string, lang: Lang): string {
  const date = new Date(iso.length === 10 ? iso + 'T00:00:00' : iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(LOCALES[lang], { day: 'numeric', month: 'short', year: 'numeric', numberingSystem: 'latn' }).format(date)
}

export const speechLocale = (lang: Lang) => LOCALES[lang]
