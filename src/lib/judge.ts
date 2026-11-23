const PUNCTUATION = /[\s.,，。、；;：:！!？?·~～"'“”‘’()（）[\]【】/／\\|…—-]+/g

function toHalfWidth(text: string): string {
  return text.replace(/[\uFF01-\uFF5E]/g, (char) =>
    String.fromCharCode(char.charCodeAt(0) - 0xfee0),
  )
}

/** Compare Chinese glosses loosely: ignore spaces and punctuation, drop a trailing 的/地/得. */
export function normalizeAnswer(raw: string): string {
  let text = toHalfWidth(raw.trim().toLowerCase()).replace(PUNCTUATION, "")
  text = text.replace(/^(一个|一名|一种|一张|一件)/, "")
  if (!text) {
    text = toHalfWidth(raw.trim().toLowerCase()).replace(PUNCTUATION, "")
  }
  if (text.length > 1) text = text.replace(/(的|地|得)+$/g, "")
  return text
}

export function answerMatches(answer: string, accepted: readonly string[]): boolean {
  const guess = normalizeAnswer(answer)
  if (!guess) return false
  for (const item of accepted) {
    const target = normalizeAnswer(item)
    if (!target) continue
    if (guess === target) return true
    // "迅速" matches "迅速的"; "很喜欢" matches "喜欢".
    // "不喜欢" must not match "喜欢".
    if (guess.length >= 2 && target.includes(guess)) return true
    if (target.length >= 2 && guess.includes(target) && !isNegated(guess)) return true
  }
  return false
}

function isNegated(guess: string): boolean {
  return /^(不|没|别|非)/.test(guess)
}
