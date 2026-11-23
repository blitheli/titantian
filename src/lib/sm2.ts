import type { CardState } from "../types.ts"

/** One day, in milliseconds. */
export const DAY_MS = 24 * 60 * 60 * 1000

const MIN_EASE = 1.3

export function freshCard(): CardState {
  return {
    ease: 2.5,
    intervalDays: 0,
    due: 0,
    reps: 0,
    lapses: 0,
    lastReviewed: null,
    correct: 0,
    wrong: 0,
  }
}

/**
 * Simplified SM-2.
 *
 * Quality is 4 for a correct recall and 1 for a miss (the original scale is 0–5).
 * Ease updates with the SM-2 formula and never drops below 1.3.
 * A correct answer schedules 1 day, then 6 days, then previous interval × ease.
 * A miss clears the streak and makes the card due immediately, so the next
 * round picks it up before new words. Classic SM-2 would wait a full day.
 */
export function reviewCard(card: CardState, correct: boolean, now: number): CardState {
  const quality = correct ? 4 : 1
  const ease = nextEase(card.ease, quality)
  if (!correct) {
    return {
      ...card,
      ease,
      reps: 0,
      intervalDays: 0,
      due: now,
      lapses: card.lapses + 1,
      lastReviewed: now,
      wrong: card.wrong + 1,
    }
  }
  let intervalDays: number
  if (card.reps <= 0) intervalDays = 1
  else if (card.reps === 1) intervalDays = 6
  else intervalDays = Math.max(1, Math.round(card.intervalDays * ease))
  return {
    ...card,
    ease,
    reps: card.reps + 1,
    intervalDays,
    due: now + intervalDays * DAY_MS,
    lastReviewed: now,
    correct: card.correct + 1,
  }
}

export function nextEase(ease: number, quality: number): number {
  const delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
  const next = ease + delta
  if (!Number.isFinite(next)) return MIN_EASE
  return Math.max(MIN_EASE, Math.round(next * 100) / 100)
}

export function isIntroduced(card: CardState | undefined): card is CardState {
  return Boolean(card && card.lastReviewed != null)
}

export function isDue(card: CardState | undefined, now: number): boolean {
  return isIntroduced(card) && card.due <= now
}

export function isStable(card: CardState | undefined): boolean {
  return isIntroduced(card) && card.reps >= 2
}

export function isActiveMistake(card: CardState | undefined): boolean {
  return isIntroduced(card) && card.lapses > 0 && card.reps < 2
}

export function isRecovered(card: CardState | undefined): boolean {
  return isIntroduced(card) && card.lapses > 0 && card.reps >= 2
}
