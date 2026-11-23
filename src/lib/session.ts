import type { CardState, PromptKind, Word } from "../types.ts"
import { isActiveMistake, isDue, isIntroduced, isRecovered, isStable } from "./sm2.ts"

export type Stats = {
  total: number
  due: number
  unseen: number
  stable: number
  activeMistakes: number
  recovered: number
}

export function classify(card: CardState | undefined): PromptKind {
  if (!isIntroduced(card)) return "new"
  if (isActiveMistake(card)) return "mistake"
  return "review"
}

export function summarize(
  words: readonly { id: string }[],
  cards: Record<string, CardState>,
  now: number,
): Stats {
  const stats: Stats = {
    total: words.length,
    due: 0,
    unseen: 0,
    stable: 0,
    activeMistakes: 0,
    recovered: 0,
  }
  for (const word of words) {
    const card = cards[word.id]
    if (!isIntroduced(card)) {
      stats.unseen += 1
      continue
    }
    if (isDue(card, now)) stats.due += 1
    if (isStable(card)) stats.stable += 1
    if (isActiveMistake(card)) stats.activeMistakes += 1
    else if (isRecovered(card)) stats.recovered += 1
  }
  return stats
}

export function practicePreview(stats: Stats, size: number): string {
  if (stats.due === 0 && stats.unseen === 0) return "现在没有到期的词，也没有新词了。"
  const takeDue = Math.min(stats.due, size)
  const takeNew = Math.min(stats.unseen, Math.max(0, size - takeDue))
  if (takeDue === 0) return `这一轮学习 ${takeNew} 个新词。`
  if (takeNew === 0) return `这一轮先复习 ${takeDue} 个到期的词。`
  return `这一轮：${takeDue} 个到期的，再加 ${takeNew} 个新词。`
}

export function buildPracticeQueue(
  words: readonly { id: string }[],
  cards: Record<string, CardState>,
  now: number,
  size: number,
): string[] {
  const due = words
    .filter((word) => isDue(cards[word.id], now))
    .sort((a, b) => {
      const delta = (cards[a.id]?.due ?? 0) - (cards[b.id]?.due ?? 0)
      return delta
    })
    .map((word) => word.id)
  const fresh = words.filter((word) => !isIntroduced(cards[word.id])).map((word) => word.id)
  return due.slice(0, size).concat(fresh.slice(0, Math.max(0, size - Math.min(due.length, size))))
}

export function buildMistakeQueue(
  words: readonly { id: string }[],
  cards: Record<string, CardState>,
  now: number,
  size: number,
): string[] {
  return words
    .filter((word) => isActiveMistake(cards[word.id]))
    .sort((a, b) => {
      const aDue = (cards[a.id]?.due ?? 0) <= now ? 0 : 1
      const bDue = (cards[b.id]?.due ?? 0) <= now ? 0 : 1
      if (aDue !== bDue) return aDue - bDue
      return (cards[a.id]?.due ?? 0) - (cards[b.id]?.due ?? 0)
    })
    .slice(0, size)
    .map((word) => word.id)
}

export function nextSeeText(
  due: number,
  now: number,
  againInSession: boolean,
  correct: boolean,
): string {
  if (!correct) {
    return againInSession
      ? "这一轮后面还会再见到它，下一轮也会优先练。"
      : "下一轮会优先再练这个词。"
  }
  const days = Math.round((due - now) / (24 * 60 * 60 * 1000))
  if (days <= 1) return "大约明天还会再见到它。"
  return `大约 ${days} 天后再见到它。`
}

export function acceptedGlosses(word: Word): string[] {
  const merged = [...word.meanings, ...word.accept]
  return merged
}
