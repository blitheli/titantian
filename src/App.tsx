import { useEffect, useRef, useState } from "react"
import { words, wordById } from "./lib/bank.ts"
import { answerMatches } from "./lib/judge.ts"
import {
  acceptedGlosses,
  buildMistakeQueue,
  buildPracticeQueue,
  classify,
  nextSeeText,
  practicePreview,
  summarize,
} from "./lib/session.ts"
import { freshCard, reviewCard } from "./lib/sm2.ts"
import {
  autoSpeakEnglish,
  canListenChinese,
  canSpeak,
  listenChinese,
  speakEnglish,
  stopSpeaking,
} from "./lib/speech.ts"
import { defaultStore, loadStore, saveStore, STORAGE_KEY } from "./lib/storage.ts"
import type { LastRound, SessionMode, SessionSize, SessionState, Store, Word } from "./types.ts"

type View = "home" | "practice" | "book" | "about" | "done"

const KIND_LABEL = {
  new: "新词",
  mistake: "错词",
  review: "复习",
} as const

export default function App() {
  const [store, setStore] = useState(loadStore)
  const storeRef = useRef(store)
  const [view, setView] = useState<View>(() => (loadStore().session ? "practice" : "home"))
  const [summary, setSummary] = useState<LastRound | null>(null)
  const [now, setNow] = useState(() => Date.now())

  function commit(recipe: (prev: Store) => Store) {
    const next = recipe(storeRef.current)
    storeRef.current = next
    saveStore(next)
    setStore(next)
    setNow(Date.now())
  }

  function startSession(mode: SessionMode) {
    const current = storeRef.current
    if (current.session) {
      setView("practice")
      return
    }
    const now = Date.now()
    const queue =
      mode === "practice"
        ? buildPracticeQueue(words, current.cards, now, current.sessionSize)
        : buildMistakeQueue(words, current.cards, now, current.sessionSize)
    if (queue.length === 0) return
    const first = queue[0]
    const session: SessionState = {
      mode,
      queue,
      index: 0,
      requeues: {},
      phase: "ask",
      promptKind: classify(first ? current.cards[first] : undefined),
      correct: null,
      answer: "",
      skipped: false,
      againInSession: false,
      roundCorrect: 0,
      roundWrong: 0,
    }
    commit(() => ({ ...current, session }))
    setView("practice")
    // 第一次朗读放在点击里同步触发，避免 iPhone 把后续自动发音静音。
    const firstWord = first ? wordById.get(first) : undefined
    if (firstWord) autoSpeakEnglish(firstWord.word)
  }

  function grade(correct: boolean, skipped: boolean, answer: string) {
    commit((prev) => {
      const session = prev.session
      if (!session || session.phase !== "ask") return prev
      const id = session.queue[session.index]
      if (!id) return prev
      const now = Date.now()
      const nextCard = reviewCard(prev.cards[id] ?? freshCard(), correct, now)
      const times = session.requeues[id] ?? 0
      let queue = session.queue
      let requeues = session.requeues
      let againInSession = false
      if (!correct && times < 2) {
        const insertAt = Math.min(session.index + 4, queue.length)
        queue = queue.slice(0, insertAt).concat(id, queue.slice(insertAt))
        requeues = { ...requeues, [id]: times + 1 }
        againInSession = true
      }
      return {
        ...prev,
        cards: { ...prev.cards, [id]: nextCard },
        session: {
          ...session,
          queue,
          requeues,
          phase: "result",
          correct,
          answer: skipped ? "" : answer,
          skipped,
          againInSession,
          roundCorrect: session.roundCorrect + (correct ? 1 : 0),
          roundWrong: session.roundWrong + (correct ? 0 : 1),
        },
      }
    })
  }

  function goNext() {
    const session = storeRef.current.session
    if (!session || session.phase !== "result") return
    if (session.index + 1 >= session.queue.length) {
      stopSpeaking()
      const finished: LastRound = {
        correct: session.roundCorrect,
        wrong: session.roundWrong,
        at: Date.now(),
      }
      commit((prev) => ({ ...prev, session: null, lastRound: finished }))
      setSummary(finished)
      setView("done")
      return
    }
    const index = session.index + 1
    const nextId = session.queue[index]
    const nextWord = nextId ? wordById.get(nextId) : undefined
    commit((prev) => {
      const current = prev.session
      if (!current) return prev
      return {
        ...prev,
        session: {
          ...current,
          index,
          phase: "ask",
          promptKind: classify(nextId ? prev.cards[nextId] : undefined),
          correct: null,
          answer: "",
          skipped: false,
          againInSession: false,
        },
      }
    })
    // 跟着「下一个」的点击同步朗读，避免 iPhone 把自动发音静音。
    if (nextWord) autoSpeakEnglish(nextWord.word)
  }

  function abandon() {
    stopSpeaking()
    commit((prev) => ({ ...prev, session: null }))
    setView("home")
  }

  function clearProgress() {
    const fresh = defaultStore()
    storeRef.current = fresh
    saveStore(fresh)
    setSummary(null)
    setStore(fresh)
    setNow(Date.now())
    setView("home")
  }

  const stats = summarize(words, store.cards, now)

  return (
    <div className="app">
      <BrandHeader prominent={view === "home"} />
      {view === "home" && (
        <Home
          store={store}
          due={stats.due}
          unseen={stats.unseen}
          stable={stats.stable}
          mistakes={stats.activeMistakes}
          total={stats.total}
          onStart={() => startSession("practice")}
          onBook={() => setView("book")}
          onAbout={() => setView("about")}
          onSize={(sessionSize) => commit((prev) => ({ ...prev, sessionSize }))}
        />
      )}
      {view === "practice" && store.session && (
        <Practice
          key={`${store.session.index}:${store.session.phase}`}
          session={store.session}
          cards={store.cards}
          now={now}
          onGrade={grade}
          onNext={goNext}
          onHome={() => {
            stopSpeaking()
            setView("home")
          }}
          onAbandon={abandon}
        />
      )}
      {view === "book" && (
        <Book
          store={store}
          activeCount={stats.activeMistakes}
          onBack={() => setView("home")}
          onReview={() => startSession("mistakes")}
        />
      )}
      {view === "about" && (
        <About onBack={() => setView("home")} onClear={clearProgress} total={stats.total} />
      )}
      {view === "done" && (
        <Done
          summary={summary ?? store.lastRound}
          onAgain={() => startSession("practice")}
          onBook={() => setView("book")}
          onHome={() => setView("home")}
        />
      )}
    </div>
  )
}

function BrandHeader({ prominent }: { prominent: boolean }) {
  const name = "李若天英语训练营"
  return (
    <header className={prominent ? "brand prominent" : "brand"}>
      <img
        className="avatar"
        src={`${import.meta.env.BASE_URL}avatar.jpg`}
        alt="李若天"
        width={prominent ? 76 : 40}
        height={prominent ? 76 : 40}
      />
      {prominent ? <h1 className="brand-name">{name}</h1> : <p className="brand-name">{name}</p>}
    </header>
  )
}

function Home({
  store,
  due,
  unseen,
  stable,
  mistakes,
  total,
  onStart,
  onBook,
  onAbout,
  onSize,
}: {
  store: Store
  due: number
  unseen: number
  stable: number
  mistakes: number
  total: number
  onStart: () => void
  onBook: () => void
  onAbout: () => void
  onSize: (size: SessionSize) => void
}) {
  const ongoing = store.session
  const preview = practicePreview({ total, due, unseen, stable, activeMistakes: mistakes, recovered: 0 }, store.sessionSize)
  const nothingLeft = !ongoing && due === 0 && unseen === 0
  return (
    <main>
      <p className="lead">先看英文，想起中文。答错的词很快会再出现；连续答对，就会隔得更久。</p>
      <button className="primary" type="button" data-testid="start-practice" onClick={onStart} disabled={nothingLeft}>
        {ongoing ? "继续这一轮" : "开始练习"}
      </button>
      <p className="note">
        {ongoing
          ? `这一轮做到第 ${ongoing.index + 1} 个，共 ${ongoing.queue.length} 个。`
          : nothingLeft
            ? mistakes > 0
              ? "错词还没到复习时间。可以先休息，或到错词本里提前复习。"
              : "现在没有到期的词。休息一下，到时间再来。"
            : preview}
      </p>
      <button className="secondary" type="button" data-testid="mistake-book" onClick={onBook}>
        错词本
        {mistakes > 0 && <span className="badge">{mistakes}</span>}
      </button>
      <section className="stats" aria-label="学习进度">
        <Stat value={due} label="到期" caption="现在该复习" />
        <Stat value={unseen} label="还没学" caption="还没练过" />
        <Stat value={stable} label="已稳住" caption="连续答对 2 次" />
      </section>
      {store.lastRound && (
        <p className="quiet">
          最近一轮：答对 {store.lastRound.correct} 次，答错 {store.lastRound.wrong} 次。
        </p>
      )}
      <fieldset className="size-box">
        <legend>一轮练几个</legend>
        <div className="chips" role="radiogroup" aria-label="一轮练几个">
          {([10, 20, 30] as const).map((size) => (
            <button
              key={size}
              type="button"
              role="radio"
              aria-checked={store.sessionSize === size}
              className={store.sessionSize === size ? "chip on" : "chip"}
              onClick={() => onSize(size)}
            >
              {size}
            </button>
          ))}
        </div>
        <p className="quiet">练完可以马上再来一轮。没有「今天只能练这些」的限制。</p>
      </fieldset>
      <p className="quiet">词库共 {total} 个，从最常见的词开始。进度只保存在这台浏览器里。</p>
      <button className="text-btn" type="button" onClick={onAbout}>
        怎么记这些词
      </button>
    </main>
  )
}

function Stat({ value, label, caption }: { value: number; label: string; caption: string }) {
  return (
    <div className="stat">
      <b>{value}</b>
      <span>{label}</span>
      <small>{caption}</small>
    </div>
  )
}

function Practice({
  session,
  cards,
  now,
  onGrade,
  onNext,
  onHome,
  onAbandon,
}: {
  session: SessionState
  cards: Store["cards"]
  now: number
  onGrade: (correct: boolean, skipped: boolean, answer: string) => void
  onNext: () => void
  onHome: () => void
  onAbandon: () => void
}) {
  const id = session.queue[session.index] ?? ""
  const word = wordById.get(id)
  const [draft, setDraft] = useState("")
  const [hint, setHint] = useState("")
  const [listening, setListening] = useState(false)
  const [speechNote, setSpeechNote] = useState("")
  const [confirmStop, setConfirmStop] = useState(false)
  const stopRef = useRef<(() => void) | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const checkRef = useRef<HTMLButtonElement>(null)
  const draftRef = useRef("")
  const enterCommitted = useRef(false)
  const listenOk = canListenChinese()

  useEffect(() => {
    if (session.phase === "ask") inputRef.current?.focus()
  }, [session.phase])

  useEffect(() => {
    if (session.phase !== "ask" || !word) return
    autoSpeakEnglish(word.word, (message) => {
      if (message) setSpeechNote(message)
    })
  }, [id, session.phase, word])

  function rememberDraft(value: string) {
    draftRef.current = value
    setDraft(value)
  }

  function focusCheck() {
    // 等本次回车结束再移动焦点，避免输入法确认和「对一下」被同一次按键一起触发。
    window.setTimeout(() => {
      const button = checkRef.current
      if (!button) return
      const until = performance.now() + 40
      const swallowEcho = (event: KeyboardEvent) => {
        if (event.key !== "Enter" && event.key !== " ") return
        if (performance.now() > until) return
        event.preventDefault()
        event.stopPropagation()
      }
      button.addEventListener("keydown", swallowEcho, true)
      button.focus()
      window.setTimeout(() => button.removeEventListener("keydown", swallowEcho, true), 50)
    }, 0)
  }

  function stopListen() {
    stopRef.current?.()
    stopRef.current = null
    setListening(false)
  }

  useEffect(() => {
    return () => {
      stopRef.current?.()
      // 不在这里 stopSpeaking：切到下一词时，点击里已启动的自动发音不要被卸载打断。
    }
  }, [])

  if (!word) {
    return (
      <main>
        <p>这个词暂时找不到。</p>
        <button className="primary" type="button" onClick={onHome}>
          返回
        </button>
      </main>
    )
  }

  function submit() {
    const answer = draft.trim()
    if (!answer) {
      setHint("先写一个中文意思。想不起来可以点「我还不会」。")
      return
    }
    stopListen()
    stopSpeaking()
    inputRef.current?.blur()
    onGrade(answerMatches(answer, acceptedGlosses(word as Word)), false, answer)
  }

  function giveUp() {
    stopListen()
    stopSpeaking()
    inputRef.current?.blur()
    onGrade(false, true, "")
  }

  function toggleListen() {
    if (listening) {
      stopListen()
      return
    }
    setSpeechNote("请说中文意思。说完可以改一改，再点「对一下」。")
    const stop = listenChinese({
      onText: (text) => {
        if (text) rememberDraft(text)
      },
      onError: (message) => {
        if (message) setSpeechNote(message)
        setListening(false)
      },
      onEnd: () => {
        setListening(false)
        if (draftRef.current.trim()) focusCheck()
      },
    })
    if (!stop) {
      setSpeechNote("这台浏览器不能语音输入，直接打字就行。")
      return
    }
    stopRef.current = stop
    setListening(true)
  }

  const last = session.index >= session.queue.length - 1
  const card = session
  return (
    <main className="practice">
      <header className="bar">
        <button className="text-btn" type="button" onClick={onHome}>
          返回
        </button>
        <span className="progress">
          {session.index + 1} / {session.queue.length}
        </span>
        <span className={`kind ${session.promptKind}`}>{KIND_LABEL[session.promptKind]}</span>
      </header>
      <div className="meter" aria-hidden="true">
        <span style={{ width: `${((session.index + (session.phase === "result" ? 1 : 0)) / session.queue.length) * 100}%` }} />
      </div>
      <p className={`word${word.word.length > 12 ? " long" : ""}`} data-testid="word-text">
        {word.word}
      </p>
      <p className="phonetic">
        {word.pos && <span className="pos">{word.pos}</span>}
        {word.phonetic && <span>/{word.phonetic}/</span>}
      </p>
      {word.example && (
        <p className="prompt-example" data-testid="word-example">
          {word.example}
        </p>
      )}
      <button
        className="listen"
        type="button"
        onClick={() => {
          setSpeechNote("")
          if (!speakEnglish(word.word, setSpeechNote)) setSpeechNote("这台设备暂时读不出英文，可以看上面的音标。")
        }}
        disabled={!canSpeak()}
      >
        听发音
      </button>

      {session.phase === "ask" ? (
        <form
          onSubmit={(event) => {
            event.preventDefault()
            const field = inputRef.current
            if (field && document.activeElement === field && field.value.trim()) {
              focusCheck()
              return
            }
            submit()
          }}
        >
          <label className="field-label" htmlFor="answer">
            它的中文意思
          </label>
          <input
            id="answer"
            ref={inputRef}
            className="answer"
            value={draft}
            placeholder="写在这里"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            lang="zh-CN"
            enterKeyHint="next"
            onChange={(event) => {
              rememberDraft(event.target.value)
              if (hint) setHint("")
            }}
            onKeyDown={(event) => {
              if (event.key !== "Enter") {
                enterCommitted.current = false
                return
              }
              if (event.nativeEvent.isComposing || event.nativeEvent.keyCode === 229) {
                enterCommitted.current = true
                return
              }
              if (!event.currentTarget.value.trim()) return
              event.preventDefault()
              focusCheck()
            }}
            onCompositionEnd={(event) => {
              if (!enterCommitted.current) return
              enterCommitted.current = false
              if (!event.currentTarget.value.trim()) return
              focusCheck()
            }}
          />
          <div className="row">
            <button className="secondary" type="button" onClick={toggleListen} disabled={!listenOk}>
              {listening ? "停一下" : "说它的意思"}
            </button>
            <button ref={checkRef} className="primary tight" type="submit" data-testid="submit-answer">
              对一下
            </button>
          </div>
          {!listenOk && <p className="quiet">这台浏览器不能语音输入，直接打字就行。</p>}
          {speechNote && <p className="quiet">{speechNote}</p>}
          {hint && <p className="hint">{hint}</p>}
          <button className="text-btn" type="button" data-testid="give-up" onClick={giveUp}>
            我还不会
          </button>
        </form>
      ) : (
        <Result
          word={word}
          session={card}
          due={cards[id]?.due ?? now}
          now={now}
          onNext={onNext}
          last={last}
        />
      )}

      {!confirmStop ? (
        <button className="text-btn muted" type="button" onClick={() => setConfirmStop(true)}>
          先停在这里
        </button>
      ) : (
        <div className="confirm">
          <p>练过的都会留下。这一轮剩下的先不练了。</p>
          <div className="row">
            <button className="secondary" type="button" onClick={() => setConfirmStop(false)}>
              继续练
            </button>
            <button className="secondary" type="button" onClick={onAbandon}>
              结束这一轮
            </button>
          </div>
        </div>
      )}
    </main>
  )
}

function Result({
  word,
  session,
  due,
  now,
  onNext,
  last,
}: {
  word: Word
  session: SessionState
  due: number
  now: number
  onNext: () => void
  last: boolean
}) {
  const correct = session.correct === true
  const nextRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    nextRef.current?.focus()
  }, [])
  return (
    <section className={correct ? "result good" : "result bad"} aria-live="polite">
      <h2>{correct ? "对，就是这个意思。" : session.skipped ? "想不起来也没关系。" : "这次没对上，没关系。"}</h2>
      {!correct && !session.skipped && session.answer && (
        <p className="yours">
          你写的是「{session.answer}」
        </p>
      )}
      <p className="meanings">{word.meanings.join("  ·  ")}</p>
      <p className="quiet">{nextSeeText(due, now, session.againInSession, correct)}</p>
      <button ref={nextRef} className="primary" type="button" data-testid="next-card" onClick={onNext}>
        {last ? "完成本轮" : "下一个"}
      </button>
    </section>
  )
}

function Book({
  store,
  activeCount,
  onBack,
  onReview,
}: {
  store: Store
  activeCount: number
  onBack: () => void
  onReview: () => void
}) {
  const [query, setQuery] = useState("")
  const [openId, setOpenId] = useState<string | null>(null)
  const needle = query.trim().toLowerCase()
  const active = words.filter((word) => {
    const card = store.cards[word.id]
    return card && card.lapses > 0 && card.reps < 2
  })
  const recovered = words.filter((word) => {
    const card = store.cards[word.id]
    return card && card.lapses > 0 && card.reps >= 2
  })
  const filtered = (list: typeof words) =>
    list.filter((word) => {
      if (!needle) return true
      return (
        word.word.toLowerCase().includes(needle) ||
        word.meanings.some((meaning) => meaning.toLowerCase().includes(needle))
      )
    })
  const activeShown = filtered(active).sort(
    (a, b) => (store.cards[a.id]?.due ?? 0) - (store.cards[b.id]?.due ?? 0),
  )
  const recoveredShown = filtered(recovered)
  return (
    <main>
      <header className="bar">
        <button className="text-btn" type="button" onClick={onBack}>
          返回
        </button>
        <h1 className="bar-title">错词本</h1>
      </header>
      <p className="rule">
        答错过、还没连续答对 2 次的词在这里。到了复习时间，开始练习会自动带上它们。连续答对 2 次后，记为「已找回」。
      </p>
      {store.session ? (
        <button className="primary" type="button" onClick={onReview}>
          先继续未完成的一轮
        </button>
      ) : (
        <button className="primary" type="button" onClick={onReview} disabled={activeCount === 0}>
          {activeCount > 0 ? `复习还没稳住的 ${Math.min(activeCount, store.sessionSize)} 个` : "还没有要复习的错词"}
        </button>
      )}
      <label className="field-label" htmlFor="find">
        查找
      </label>
      <input
        id="find"
        className="answer"
        value={query}
        placeholder="英文或中文"
        onChange={(event) => setQuery(event.target.value)}
      />
      {activeShown.length === 0 ? (
        <p className="empty">
          {active.length === 0
            ? "还没有错词。练习时没对上的词会记在这里。"
            : "没有找到这个词。"}
        </p>
      ) : (
        <ul className="list">
          {activeShown.map((word) => {
            const card = store.cards[word.id]
            const open = openId === word.id
            const left = card && card.reps >= 1 ? "再答对 1 次就稳住" : "还要答对 2 次"
            return (
              <li key={word.id}>
                <button
                  className={open ? "item open" : "item"}
                  type="button"
                  onClick={() => setOpenId(open ? null : word.id)}
                >
                  <span className="item-word">{word.word}</span>
                  <span className="item-meta">
                    {word.phonetic ? `/${word.phonetic}/ · ` : ""}
                    {left}
                  </span>
                  {open && <span className="item-meaning">{word.meanings.join(" · ")}</span>}
                </button>
              </li>
            )
          })}
        </ul>
      )}
      {recoveredShown.length > 0 && (
        <details className="recovered">
          <summary>已找回（{recoveredShown.length}）</summary>
          <ul className="list">
            {recoveredShown.map((word) => (
              <li key={word.id}>
                <button
                  className={openId === word.id ? "item open" : "item"}
                  type="button"
                  onClick={() => setOpenId(openId === word.id ? null : word.id)}
                >
                  <span className="item-word">{word.word}</span>
                  <span className="item-meta">已连续答对</span>
                  {openId === word.id && <span className="item-meaning">{word.meanings.join(" · ")}</span>}
                </button>
              </li>
            ))}
          </ul>
        </details>
      )}
    </main>
  )
}

function About({
  onBack,
  onClear,
  total,
}: {
  onBack: () => void
  onClear: () => void
  total: number
}) {
  const [confirm, setConfirm] = useState(false)
  return (
    <main className="about">
      <header className="bar">
        <button className="text-btn" type="button" onClick={onBack}>
          返回
        </button>
        <h1 className="bar-title">怎么记</h1>
      </header>
      <p className="lead">先看英文，自己回忆中文。对了或没对上，马上告诉你。</p>
      <h2>间隔</h2>
      <ul className="plain">
        <li>新词答对：大约 1 天后再见。</li>
        <li>再连续答对一次：大约 6 天。</li>
        <li>之后每次再答对，间隔大约乘上熟练度。熟练度从 2.5 开始，答错会降低，最低 1.3。</li>
        <li>答错：连续答对次数清零，这个词马上到期，下一轮会优先再练。同一轮里，它还会在后面再出现，最多 2 次。</li>
      </ul>
      <p className="quiet">
        这是简化的 SM-2。答对按 4 分、答错按 1 分更新熟练度。答错后没有按经典算法再等一整天，而是下一轮就优先出现。
      </p>
      <h2>错词本</h2>
      <p>
        曾经答错、还没连续答对 2 次的词算「还没稳住」。到期后会自动进练习；也可以在错词本里提前复习，答对同样算数。连续答对 2 次后记为「已找回」。
      </p>
      <h2>怎么算对</h2>
      <p>写对一个主要意思即可。快的、迅速的这类常见说法都算对，多写的「的」可以不写。只写反义词不算对。</p>
      <h2>词库</h2>
      <p>
        共 {total} 个中考常考词，按使用频率从高到低排列，最常见的词先出现。读音是词典音标整理成的提示，可能和课本不完全一样。
      </p>
      <h2>语音</h2>
      <p>
        单词出现时会自动读一次；「听发音」可以再听。用的是这台设备自己的英语语音，不经过服务器。iPhone 侧边静音时没有声音。在微信里打开也经常没有声音，用 Safari、Chrome 或 Edge 打开即可。「说它的意思」用语音识别，安卓 Chrome 通常可以用。iPhone 上经常没有这项功能，直接打字就行。识别结果可以先改再提交。
      </p>
      <h2>进度存在哪里</h2>
      <p>
        只存在这台浏览器的 localStorage，键名是 {STORAGE_KEY}。不登录，不上传。换浏览器，或清除这个网站的数据，进度会消失。
      </p>
      {!confirm ? (
        <button className="text-btn danger" type="button" onClick={() => setConfirm(true)}>
          清除这台浏览器里的进度
        </button>
      ) : (
        <div className="confirm">
          <p>真的清除？练过的词会全部忘掉。</p>
          <div className="row">
            <button className="secondary" type="button" onClick={() => setConfirm(false)}>
              取消
            </button>
            <button className="secondary" type="button" onClick={onClear}>
              清除
            </button>
          </div>
        </div>
      )}
    </main>
  )
}

function Done({
  summary,
  onAgain,
  onBook,
  onHome,
}: {
  summary: LastRound | null
  onAgain: () => void
  onBook: () => void
  onHome: () => void
}) {
  return (
    <main>
      <p className="kicker">这一轮练完了</p>
      <h1>先到这里</h1>
      {summary && (
        <p className="lead">
          答对 {summary.correct} 次，答错 {summary.wrong} 次。
        </p>
      )}
      <p>答错的词已经记好了。再开一轮时，它们会排在新词前面。</p>
      <button className="primary" type="button" onClick={onAgain}>
        再来一轮
      </button>
      <button className="secondary" type="button" onClick={onBook}>
        看看错词
      </button>
      <button className="text-btn" type="button" onClick={onHome}>
        回首页
      </button>
    </main>
  )
}
