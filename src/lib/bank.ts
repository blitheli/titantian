import raw from "../data/words.json"
import type { Word } from "../types.ts"

type BankFile = {
  words: Word[]
}

export const words: Word[] = (raw as BankFile).words
export const wordById: ReadonlyMap<string, Word> = new Map(words.map((word) => [word.id, word]))
