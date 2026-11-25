type SpeechResultEvent = Event & {
  resultIndex: number
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }>
}

type SpeechErrorEvent = Event & { error?: string }

type Recognition = {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: SpeechResultEvent) => void) | null
  onerror: ((event: SpeechErrorEvent) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

type RecognitionCtor = new () => Recognition

function recognitionCtor(): RecognitionCtor | null {
  const host = window as Window & {
    SpeechRecognition?: RecognitionCtor
    webkitSpeechRecognition?: RecognitionCtor
  }
  return host.SpeechRecognition ?? host.webkitSpeechRecognition ?? null
}

export function canListenChinese(): boolean {
  return recognitionCtor() != null
}

export function canSpeak(): boolean {
  return typeof window.speechSynthesis !== "undefined"
}

export type EnglishVoice = {
  lang: string
  localService?: boolean
}

export function pickEnglishVoice<T extends EnglishVoice>(voices: readonly T[]): T | null {
  const english = voices.filter((voice) => voiceLang(voice).startsWith("en"))
  let best: T | null = null
  let bestScore = -1
  for (const voice of english) {
    const lang = voiceLang(voice)
    const local = voice.localService === false ? 0 : 2
    const region = lang.startsWith("en-us") ? 2 : 1
    const score = local * 10 + region
    if (score > bestScore) {
      best = voice
      bestScore = score
    }
  }
  return best
}

function voiceLang(voice: EnglishVoice): string {
  return voice.lang.toLowerCase().replace(/_/g, "-")
}

let speakTimer = 0
let speakRun = 0
let activeUtterance: SpeechSynthesisUtterance | null = null

export function stopSpeaking(): void {
  window.clearTimeout(speakTimer)
  speakRun += 1
  activeUtterance = null
  window.speechSynthesis?.cancel()
}

export function speakEnglish(text: string, onError?: (message: string) => void): boolean {
  if (!text || !canSpeak()) return false
  const synth = window.speechSynthesis
  window.clearTimeout(speakTimer)
  const voice = pickEnglishVoice(synth.getVoices())

  const begin = (chosen: SpeechSynthesisVoice | null, allowFallback: boolean) => {
    const run = ++speakRun
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = chosen ? voiceLang(chosen) : "en-US"
    utterance.rate = 0.86
    if (chosen) {
      try {
        utterance.voice = chosen
      } catch {
        utterance.lang = "en-US"
      }
    }
    activeUtterance = utterance
    utterance.onend = () => {
      if (activeUtterance === utterance) activeUtterance = null
    }
    utterance.onerror = (event) => {
      if (run !== speakRun) return
      if (event.error === "interrupted" || event.error === "canceled") return
      const remoteFailed =
        chosen?.localService === false &&
        (event.error === "network" || event.error === "synthesis-failed" || event.error === "synthesis-unavailable")
      if (allowFallback && remoteFailed) {
        const local = pickEnglishVoice(synth.getVoices().filter((item) => item.localService !== false))
        begin(local && local.localService !== false ? local : null, false)
        return
      }
      onError?.(speechErrorText(event.error))
    }
    if (synth.paused) synth.resume()
    try {
      synth.speak(utterance)
    } catch {
      if (run === speakRun) onError?.(speechErrorText("synthesis-unavailable"))
    }
  }

  // 空闲时不要 cancel()：Chrome 会把紧接着的 speak() 吞掉。
  // 第一次朗读必须在点击里同步调用，否则 iPhone 会直接静音。
  if (synth.speaking || synth.pending) {
    synth.cancel()
    speakTimer = window.setTimeout(() => begin(voice, true), 50)
  } else {
    begin(voice, true)
  }
  return true
}

function speechErrorText(code: string): string {
  switch (code) {
    case "network":
      return "在线英语语音没有连上。可以看上面的音标，或换 Safari、Chrome、Edge 打开。"
    case "not-allowed":
      return "浏览器拦住了朗读。请再点一次「听发音」。"
    case "audio-hardware":
    case "audio-busy":
      return "没有找到能出声的设备。请检查是否静音，以及音量。"
    case "language-unavailable":
    case "voice-unavailable":
    case "synthesis-unavailable":
    case "synthesis-failed":
      return "这台设备没有可用的英语语音，可以看上面的音标。"
    default:
      return "这台设备暂时读不出英文，可以看上面的音标。"
  }
}

export function listenChinese(handlers: {
  onText: (text: string) => void
  onError: (message: string) => void
  onEnd: () => void
}): (() => void) | null {
  const Ctor = recognitionCtor()
  if (!Ctor) return null
  const recognition = new Ctor()
  recognition.lang = "zh-CN"
  recognition.continuous = false
  recognition.interimResults = true
  recognition.onresult = (event) => {
    let text = ""
    for (let index = 0; index < event.results.length; index += 1) {
      text += event.results[index]?.[0]?.transcript ?? ""
    }
    handlers.onText(text.trim())
  }
  recognition.onerror = (event) => {
    handlers.onError(listenError(event.error))
  }
  recognition.onend = () => handlers.onEnd()
  try {
    recognition.start()
  } catch {
    handlers.onError("语音这会儿用不了。直接打字就行。")
    return null
  }
  return () => {
    recognition.onend = null
    try {
      recognition.abort()
    } catch {
      // Already stopped.
    }
  }
}

function listenError(code: string | undefined): string {
  switch (code) {
    case "not-allowed":
    case "service-not-allowed":
      return "没有拿到麦克风权限。直接打字就行。"
    case "no-speech":
      return "没听清。可以再说一次，或直接打字。"
    case "network":
      return "语音识别需要联网。这会儿可以先打字。"
    case "audio-capture":
      return "没有找到麦克风。直接打字就行。"
    case "aborted":
      return ""
    default:
      return "语音这会儿用不了。直接打字就行。"
  }
}

if (typeof window !== "undefined" && window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices()
  }
  window.speechSynthesis.getVoices()
}
