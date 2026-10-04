// Small shared pieces: icons, buttons, and the loading / error / empty states used on every page.
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useStore } from '../lib/store'

const PATHS: Record<string, string> = {
  check: 'M4 12.5l5 5L20 6.5',
  cross: 'M6 6l12 12M18 6L6 18',
  question: 'M9 9a3 3 0 115 2.2c-1 .8-2 1.4-2 2.8M12 18h.01',
  step: 'M4 18h5v-5h5V8h6',
  clock: 'M12 7v5l3 2M12 21a9 9 0 100-18 9 9 0 000 18z',
  mic: 'M12 15a3 3 0 003-3V6a3 3 0 10-6 0v6a3 3 0 003 3zM6 11a6 6 0 0012 0M12 17v4',
  link: 'M14 5h5v5M19 5l-8 8M11 7H6v11h11v-5',
  alert: 'M12 9v4M12 17h.01M10.3 4.3L2.8 17a2 2 0 001.7 3h15a2 2 0 001.7-3L13.7 4.3a2 2 0 00-3.4 0z',
  back: 'M15 5l-7 7 7 7',
  sound: 'M4 10v4h4l5 4V6L8 10H4zM16 9a4 4 0 010 6',
  download: 'M12 4v11M7 11l5 5 5-5M5 20h14',
}

export function Icon({ name, className = 'h-5 w-5' }: { name: keyof typeof PATHS | string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"
      strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  )
}

type Variant = 'primary' | 'quiet' | 'chip'
const VARIANTS: Record<Variant, string> = {
  primary: 'bg-ink text-sheet px-5 font-semibold hover:bg-ink/90 disabled:bg-soft/50',
  quiet: 'border border-ink/30 bg-sheet px-4 font-medium hover:border-ink disabled:opacity-50',
  chip: 'border border-ink/30 bg-sheet px-4 hover:border-ink hover:bg-paper rounded-full',
}

export function Button({ variant = 'quiet', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type="button" {...props}
    className={`tap inline-flex items-center justify-center gap-2 rounded-md text-base transition-colors ${VARIANTS[variant]} ${className}`} />
}

export function Loading({ label }: { label?: string }) {
  const { t } = useStore()
  return (
    <div role="status" className="flex items-center gap-3 py-8 text-soft">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-rule border-t-ink" />
      {label ?? t('state.loading')}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useStore()
  const offline = message === 'offline'
  return (
    <div role="alert" className="my-4 border-l-4 border-sindoor bg-sindoor-wash p-4">
      <p className="flex items-start gap-2 font-semibold text-sindoor"><Icon name="alert" className="mt-0.5 h-5 w-5 shrink-0" />
        {offline ? t('state.offline') : t('state.error')}</p>
      <p className="mt-1 text-sm">{offline ? t('state.offline_help') : message}</p>
      {onRetry && <Button className="mt-3" onClick={onRetry}>{t('state.retry')}</Button>}
    </div>
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="border border-dashed border-rule p-6 text-center">
      <p className="font-semibold">{title}</p>
      {children && <div className="mt-2 text-soft">{children}</div>}
    </div>
  )
}

// Shown on pages that need a profile when there is none yet.
export function NeedProfile() {
  const { t } = useStore()
  return (
    <EmptyState title={t('state.no_profile')}>
      <p>{t('state.no_profile_help')}</p>
      <Link to="/" className="tap mt-4 inline-flex items-center rounded-md bg-ink px-5 font-semibold text-sheet">{t('nav.profile')}</Link>
    </EmptyState>
  )
}

export function PageTitle({ title, lead, back }: { title: string; lead?: string; back?: string }) {
  const { t } = useStore()
  return (
    <header className="mb-5">
      {back && <Link to={back} className="tap -ml-1 inline-flex items-center gap-1 text-soft hover:text-ink"><Icon name="back" className="h-4 w-4" />{t('nav.back')}</Link>}
      <h1 className="text-[1.75rem] sm:text-[2.1rem]">{title}</h1>
      {lead && <p className="mt-2 max-w-[62ch] text-soft">{lead}</p>}
    </header>
  )
}
