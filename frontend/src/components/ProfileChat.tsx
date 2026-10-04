// The 2-minute profile chat. The backend ranks which field to ask next; answers are chips,
// typed text or voice. Free text is read by /api/extract (LLM, or keyword mock when offline).
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { optionLabel } from '../i18n'
import { api } from '../lib/api'
import { formatINR, speechLocale } from '../lib/format'
import { QUESTIONS, type Question } from '../lib/questions'
import { useStore } from '../lib/store'
import type { Profile, ProfileValue } from '../lib/types'
import { Button, Icon } from './ui'

interface Message { from: 'bot' | 'me'; text: string }

const UNITS: [RegExp, number][] = [
  [/crore|cr\b|ಕೋಟಿ|करोड़/i, 10000000], [/lakh|lac|ಲಕ್ಷ|लाख/i, 100000], [/thousand|\bk\b|ಸಾವಿರ|हज़ार|हजार/i, 1000],
]

// "8 lakh", "25,000", "4.5 लाख" -> rupees. Returns null if the text is not just an amount.
export function parseAmount(text: string): number | null {
  const match = text.trim().match(/^(?:₹|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?)\s*([^\d\s].*)?$/i)
  if (!match) return null
  const number = parseFloat(match[1].replace(/,/g, ''))
  const unit = match[2]?.trim()
  if (!unit) return Math.round(number)
  const found = UNITS.find(([pattern]) => pattern.test(unit))
  return found ? Math.round(number * found[1]) : null
}

export function showValue(t: ReturnType<typeof useStore>['t'], field: string, value: ProfileValue): string {
  if (typeof value === 'boolean') return t(value ? 'answer.yes' : 'answer.no')
  if (typeof value === 'number') return field.endsWith('_inr') ? formatINR(value) : String(value)
  if (typeof value === 'string') return QUESTIONS[field]?.kind === 'choice' ? optionLabel(t, value) : value
  return ''
}

function MicButton({ onText }: { onText: (text: string) => void }) {
  const { t, lang } = useStore()
  const [listening, setListening] = useState(false)
  const [failed, setFailed] = useState(false)
  // Browser speech recognition (Chrome, Edge). It needs the internet; typing always works.
  const Recognition = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition
  if (!Recognition) return null

  const start = () => {
    const recognition = new Recognition()
    recognition.lang = speechLocale(lang)
    recognition.interimResults = false
    recognition.onresult = (event: any) => onText(event.results[0][0].transcript)
    recognition.onerror = () => setFailed(true)
    recognition.onend = () => setListening(false)
    setFailed(false)
    setListening(true)
    recognition.start()
  }

  return (
    <>
      <button type="button" onClick={start} disabled={listening} aria-label={t('chat.mic')} title={t('chat.mic')}
        className={`tap inline-flex w-12 shrink-0 items-center justify-center rounded-md border ${listening ? 'border-sindoor bg-sindoor-wash text-sindoor' : 'border-ink/30 hover:border-ink'}`}>
        <Icon name="mic" />
      </button>
      <span role="status" className="sr-only">{listening ? t('chat.listening') : failed ? t('chat.mic_failed') : ''}</span>
      {failed && <span className="absolute -top-6 left-0 text-sm text-sindoor">{t('chat.mic_failed')}</span>}
    </>
  )
}

function Chips({ field, question, onAnswer }: { field: string; question: Question; onAnswer: (value: ProfileValue, shown: string) => void }) {
  const { t, skip } = useStore()
  const chips: { value: ProfileValue; label: string }[] =
    question.kind === 'bool' ? [{ value: true, label: t('answer.yes') }, { value: false, label: t('answer.no') }]
    : question.kind === 'choice' ? question.options!.map((o) => ({ value: o, label: optionLabel(t, o) }))
    : question.kind === 'money' ? question.amounts!.map((a) => ({ value: a, label: formatINR(a) }))
    : []
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {chips.map((chip) => (
        <Button key={String(chip.value)} variant="chip" onClick={() => onAnswer(chip.value, chip.label)}>{chip.label}</Button>
      ))}
      {question.sensitive
        ? <Button variant="chip" className="border-dashed" onClick={() => question.preferNot ? onAnswer(question.preferNot, t('answer.prefer_not')) : skip(field)}>{t('answer.prefer_not')}</Button>
        : <Button variant="chip" className="border-dashed text-soft" onClick={() => skip(field)}>{t('answer.skip')}</Button>}
    </div>
  )
}

export function ProfileChat() {
  const { t, lang, profile, evaluation, skipped, update, error } = useStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  const next = evaluation?.next_questions.find((q) => QUESTIONS[q.field] && !skipped.includes(q.field) && profile[q.field] == null)
  const field = next?.field
  const question = field ? QUESTIONS[field] : undefined

  useEffect(() => { endRef.current?.scrollIntoView({ block: 'nearest' }) }, [messages.length, field])

  const say = (...added: Message[]) => setMessages((m) => [...m, ...added])

  const answer = (value: ProfileValue, shown: string) => {
    if (!field) return
    say({ from: 'bot', text: t(`q.${field}`) }, { from: 'me', text: shown })
    update({ [field]: value })
  }

  const send = async (event: FormEvent) => {
    event.preventDefault()
    const typed = text.trim()
    if (!typed || busy) return
    setText('')
    // A bare amount or number answers the question on screen.
    const amount = parseAmount(typed)
    if (field && question && amount !== null && (question.kind === 'money' || question.kind === 'number')) {
      answer(amount, question.kind === 'money' ? formatINR(amount) : String(amount))
      return
    }
    say({ from: 'me', text: typed })
    setBusy(true)
    try {
      const found: Profile = (await api.extract(typed, lang)).profile
      const keys = Object.keys(found)
      if (keys.length) {
        update(found)
        say({ from: 'bot', text: t('chat.understood', { list: keys.map((k) => `${t(`field.${k}`)}: ${showValue(t, k, found[k])}`).join('; ') }) })
      } else {
        say({ from: 'bot', text: t('chat.not_understood') })
      }
    } catch {
      say({ from: 'bot', text: t('chat.extract_failed') })
    } finally {
      setBusy(false)
    }
  }

  const bubble = (m: Message, key: number | string) => (
    <div key={key} className={m.from === 'me' ? 'flex justify-end' : ''}>
      <p className={`max-w-[85%] whitespace-pre-line rounded-lg px-3.5 py-2 ${m.from === 'me' ? 'rounded-br-sm bg-ink text-sheet' : 'rounded-bl-sm bg-paper'}`}>{m.text}</p>
    </div>
  )

  return (
    <section aria-label={t('chat.title')} className="ledger flex flex-col">
      <div className="max-h-[26rem] min-h-[14rem] space-y-3 overflow-y-auto p-4" aria-live="polite">
        {bubble({ from: 'bot', text: t('chat.hello') }, 'hello')}
        {messages.map(bubble)}
        {busy && bubble({ from: 'bot', text: t('chat.reading') }, 'busy')}
        {!busy && field && question && (
          <div>
            {bubble({ from: 'bot', text: t(`q.${field}`) }, 'question')}
            {(question.sensitive || question.note) && <p className="mt-1.5 max-w-[85%] text-sm text-soft">{t(`why.${field}`)}</p>}
            <Chips field={field} question={question} onAnswer={answer} />
          </div>
        )}
        {!busy && !field && evaluation && !error && bubble({ from: 'bot', text: t('chat.done') }, 'done')}
        <div ref={endRef} />
      </div>
      <form onSubmit={send} className="relative flex gap-2 border-t border-rule p-3">
        <label htmlFor="chat-input" className="sr-only">{t('chat.placeholder')}</label>
        <input id="chat-input" value={text} onChange={(e) => setText(e.target.value)} placeholder={t('chat.placeholder')}
          autoComplete="off" className="tap min-w-0 flex-1 rounded-md border border-ink/30 bg-white px-3" />
        <MicButton onText={setText} />
        <Button type="submit" variant="primary" disabled={busy || !text.trim()}>{t('chat.send')}</Button>
      </form>
    </section>
  )
}
