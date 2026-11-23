import { wordById } from "./bank.ts"
import type { CardState, LastRound, SessionSize, SessionState, Store } from "../types.ts"

export const STORAGE_KEY = "chusan-en-vocab-v1"

const SIZES: readonly SessionSize[] = [10, 20, 30]
const KINDS = ["new", "mistake", "review"] as const

export function defaultStore(): Store {
  return {
    v: 1,
    cards: {},
    sessionSize: 20,
    session: null,
    lastRound: null,
  }
}

export function loadStore(): Store {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultStore()
    const data = JSON.parse(raw) as Partial<Store>
    if (!data || data.v !== 1) return defaultStore()
    const cards: Record<string, CardState> = {}
    if (data.cards && typeof data.cards === "object") {
      for (const [id, card] of Object.entries(data.cards)) {
        if (!wordById.has(id) || !isCard(card)) continue
        cards[id] = card
      }
    }
    return {
      v: 1,
      cards,
      sessionSize: isSize(data.sessionSize) ? data.sessionSize : 20,
      session: sanitizeSession(data.session),
      lastRound: isLastRound(data.lastRound) ? data.lastRound : null,
    }
  } catch {
    return defaultStore()
  }
}

export function saveStore(store: Store): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
  } catch {
    // A full browser quota should not block the current round.
  }
}

function isSize(value: unknown): value is SessionSize {
  return SIZES.includes(value as SessionSize)
}

function isCard(value: unknown): value is CardState {
  if (!value || typeof value !== "object") return false
  const card = value as CardState
  return (
    typeof card.ease === "number" &&
    Number.isFinite(card.ease) &&
    typeof card.intervalDays === "number" &&
    typeof card.due === "number" &&
    typeof card.reps === "number" &&
    typeof card.lapses === "number" &&
    typeof card.correct === "number" &&
    typeof card.wrong === "number" &&
    (card.lastReviewed === null || typeof card.lastReviewed === "number")
  )
}

function isLastRound(value: unknown): value is LastRound {
  if (!value || typeof value !== "object") return false
  const round = value as LastRound
  return (
    typeof round.correct === "number" &&
    typeof round.wrong === "number" &&
    typeof round.at === "number"
  )
}

function sanitizeSession(value: unknown): SessionState | null {
  if (!value || typeof value !== "object") return null
  const session = value as SessionState
  if (session.mode !== "practice" && session.mode !== "mistakes") return null
  if (session.phase !== "ask" && session.phase !== "result") return null
  if (!Array.isArray(session.queue) || session.queue.length === 0) return null
  const queue = session.queue.filter((id) => typeof id === "string" && wordById.has(id))
  if (queue.length === 0) return null
  const index = Number.isInteger(session.index) ? session.index : 0
  if (index < 0 || index >= queue.length) return null
  const requeues: Record<string, number> = {}
  if (session.requeues && typeof session.requeues === "object") {
    for (const [id, count] of Object.entries(session.requeues)) {
      if (typeof count === "number" && count > 0) requeues[id] = count
    }
  }
  const promptKind = KINDS.includes(session.promptKind) ? session.promptKind : "review"
  if (session.phase === "result" && typeof session.correct !== "boolean") return null
  return {
    mode: session.mode,
    queue,
    index,
    requeues,
    phase: session.phase,
    promptKind,
    correct: session.phase === "result" ? session.correct : null,
    answer: typeof session.answer === "string" ? session.answer : "",
    skipped: Boolean(session.skipped),
    againInSession: Boolean(session.againInSession),
    roundCorrect: typeof session.roundCorrect === "number" ? session.roundCorrect : 0,
    roundWrong: typeof session.roundWrong === "number" ? session.roundWrong : 0,
  }
}
