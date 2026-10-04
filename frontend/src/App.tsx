import { NavLink, Route, Routes } from 'react-router-dom'
import { LANGUAGES } from './i18n'
import { EmptyState } from './components/ui'
import { useStore } from './lib/store'
import type { Lang } from './lib/types'
import Admin from './pages/Admin'
import Onboard from './pages/Onboard'
import Pack from './pages/Pack'
import PathPage from './pages/PathPage'
import Project from './pages/Project'
import Results from './pages/Results'
import SchemeDetail from './pages/SchemeDetail'
import Watch from './pages/Watch'

const NAV = [
  { to: '/', key: 'nav.profile' },
  { to: '/results', key: 'nav.results' },
  { to: '/path', key: 'nav.path' },
  { to: '/watch', key: 'nav.watch' },
]

export default function App() {
  const { t, lang, setLang, consent, profile } = useStore()
  // The project report is only for new units.
  const nav = profile.is_new_project === true ? [...NAV, { to: '/project', key: 'nav.project' }] : NAV
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-10 focus:bg-card focus:p-2">{t('nav.skip')}</a>
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3">
          <NavLink to="/" className="font-serif text-2xl font-semibold tracking-tight">{t('app.name')}</NavLink>
          <label className="flex items-center gap-2 text-sm">
            <span className="sr-only">{t('welcome.language')}</span>
            <select value={lang} onChange={(e) => setLang(e.target.value as Lang)}
              className="tap rounded-md border border-border-hover bg-card px-2 text-base">
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
            </select>
          </label>
        </div>
        {consent && (
          <nav aria-label={t('nav.main')} className="mx-auto flex max-w-5xl gap-1 overflow-x-auto px-2">
            {nav.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === '/'}
                className={({ isActive }) => `tap flex shrink-0 items-center border-b-2 px-3 text-[0.95rem] font-medium tracking-wide ${isActive ? 'border-accent text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'}`}>
                {t(item.key)}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:py-14">
        <Routes>
          <Route path="/" element={<Onboard />} />
          <Route path="/results" element={<Results />} />
          <Route path="/scheme/:id" element={<SchemeDetail />} />
          <Route path="/path" element={<PathPage />} />
          <Route path="/pack/:id" element={<Pack />} />
          <Route path="/watch" element={<Watch />} />
          <Route path="/project" element={<Project />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<EmptyState title={t('state.not_found')} />} />
        </Routes>
      </main>

      <footer className="border-t border-border">
        <p className="mx-auto max-w-5xl px-4 py-6 text-sm text-muted-foreground">{t('footer.disclaimer')}</p>
      </footer>
    </div>
  )
}
