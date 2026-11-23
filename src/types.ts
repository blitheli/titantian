export type CardState = {
  ease: number
  intervalDays: number
  due: number
  reps: number
  lapses: number
  lastReviewed: number | null
  correct: number
  wrong: number
}

export type PromptKind = "new" | "mistake" | "review"

export type SessionMode = "practice" | "mistakes"

export type SessionState = {
  mode: SessionMode
  queue: string[]
  index: number
  requeues: Record<string, number>
  phase: "ask" | "result"
  promptKind: PromptKind
  correct: boolean | null
  answer: string
  skipped: boolean
  againInSession: boolean
  roundCorrect: number
  roundWrong: number
}

export type LastRound = {
  correct: number
  wrong: number
  at: number
}

export type SessionSize = 10 | 20 | 30

export type Store = {
  v: 1
  cards: Record<string, CardState>
  sessionSize: SessionSize
  session: SessionState | null
  lastRound: LastRound | null
}

export type Word = {
  id: string
  word: string
  phonetic: string
  pos?: string
  meanings: string[]
  accept: string[]
  example?: string
  exampleZh?: string
}
