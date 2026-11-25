import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { answerMatches, normalizeAnswer } from "../src/lib/judge.ts"
import { pickEnglishVoice } from "../src/lib/speech.ts"
import { freshCard, nextEase, reviewCard } from "../src/lib/sm2.ts"
import { buildMistakeQueue, buildPracticeQueue } from "../src/lib/session.ts"

const DAY = 24 * 60 * 60 * 1000
const now = 1_700_000_000_000

const first = reviewCard(freshCard(), true, now)
assert.equal(first.reps, 1)
assert.equal(first.intervalDays, 1)
assert.equal(first.due, now + DAY)
assert.equal(first.ease, 2.5)

const second = reviewCard(first, true, now + DAY)
assert.equal(second.reps, 2)
assert.equal(second.intervalDays, 6)

const third = reviewCard(second, true, now + 7 * DAY)
assert.equal(third.intervalDays, Math.round(6 * 2.5))
assert.equal(third.reps, 3)

const missed = reviewCard(third, false, now + 20 * DAY)
assert.equal(missed.reps, 0)
assert.equal(missed.lapses, 1)
assert.equal(missed.intervalDays, 0)
assert.ok(missed.due <= now + 20 * DAY)
assert.ok(missed.ease < third.ease)
assert.ok(missed.ease >= 1.3)

let ease = 2.5
for (let i = 0; i < 10; i += 1) ease = nextEase(ease, 1)
assert.equal(ease, 1.3)

const again = reviewCard(freshCard(), false, now)
const queue = buildPracticeQueue(
  [{ id: "a" }, { id: "b" }, { id: "c" }],
  { a: again, b: reviewCard(reviewCard(freshCard(), true, now), true, now) },
  now,
  2,
)
assert.deepEqual(queue, ["a", "c"])

const recovered = reviewCard(reviewCard(again, true, now), true, now + DAY)
const mistakes = buildMistakeQueue(
  [{ id: "a" }, { id: "b" }, { id: "c" }],
  {
    a: { ...again, due: now + DAY },
    b: { ...again, due: now - DAY },
    c: recovered,
  },
  now,
  10,
)
assert.deepEqual(mistakes, ["b", "a"])

assert.equal(answerMatches("迅速的", ["快的", "迅速的"]), true)
assert.equal(answerMatches("迅速", ["快的", "迅速的"]), true)
assert.equal(answerMatches("  快的 ", ["迅速的", "快的"]), true)
assert.equal(answerMatches("是的", ["是"]), true)
assert.equal(answerMatches("一个苹果", ["苹果"]), true)
assert.equal(answerMatches("不喜欢", ["喜欢"]), false)
assert.equal(answerMatches("很喜欢", ["喜欢"]), true)
assert.equal(answerMatches("苹果", ["是"]), false)
assert.equal(answerMatches("", ["是"]), false)
assert.equal(answerMatches("的", ["的"]), true)
assert.equal(normalizeAnswer("好的"), "好")

const google = { lang: "en-US", localService: false, name: "Google US English" }
const zira = { lang: "en-US", localService: true, name: "Microsoft Zira" }
const uk = { lang: "en-GB", localService: true, name: "Daniel" }
assert.equal(pickEnglishVoice([google, zira, uk])?.name, "Microsoft Zira")
assert.equal(pickEnglishVoice([uk, google])?.name, "Daniel")
assert.equal(pickEnglishVoice([{ lang: "en_US", localService: true, name: "Samantha" }])?.name, "Samantha")
assert.equal(pickEnglishVoice([{ lang: "zh-CN", localService: true, name: "Huihui" }]), null)

const bank = JSON.parse(readFileSync(new URL("../src/data/words.json", import.meta.url), "utf8")) as {
  count: number
  words: { id: string; word: string; meanings: string[]; accept: string[]; phonetic: string }[]
}
assert.ok(bank.count >= 1000, `词库只有 ${bank.count} 个`)
assert.equal(bank.words.length, bank.count)
const ids = new Set<string>()
for (const word of bank.words) {
  assert.ok(word.id && word.word)
  assert.ok(word.meanings.length > 0, word.word)
  assert.ok(word.accept.length >= word.meanings.length, word.word)
  assert.ok(!ids.has(word.id), word.id)
  ids.add(word.id)
}
assert.equal(bank.words[0]?.word.toLowerCase(), "the")
const fast = bank.words.find((word) => word.id === "fast")
assert.ok(fast)
assert.equal(answerMatches("迅速的", fast.accept.concat(fast.meanings)), true)
assert.equal(answerMatches("快", fast.accept.concat(fast.meanings)), true)

console.log(`selfcheck ok · ${bank.count} words`)
