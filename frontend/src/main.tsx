import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// Fonts are bundled with the app (no CDN), so the demo works without internet.
import '@fontsource-variable/anek-latin/wdth.css'
import '@fontsource-variable/anek-kannada/wdth.css'
import '@fontsource-variable/anek-devanagari/wdth.css'
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
