import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// Fonts are bundled with the app (no CDN), so the demo works without internet.
import '@fontsource-variable/playfair-display'
import '@fontsource-variable/source-sans-3'
import '@fontsource-variable/noto-serif-kannada'
import '@fontsource-variable/noto-serif-devanagari'
import '@fontsource-variable/noto-sans-kannada'
import '@fontsource-variable/noto-sans-devanagari'
import '@fontsource/ibm-plex-mono/latin-500.css'
import './index.css'
import App from './App'
import { StoreProvider } from './lib/store'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <StoreProvider>
        <App />
      </StoreProvider>
    </BrowserRouter>
  </StrictMode>,
)
