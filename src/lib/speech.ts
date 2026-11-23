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

let speakTimer = 0

export function stopSpeaking(): void {
  window.clearTimeout(speakTimer)
  window.speechSynthesis?.cancel()
}

export function speakEnglish(text: string): boolean {
  if (!text || !canSpeak()) return false
  const synth = window.speechSynthesis
  stopSpeaking()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = "en-US"
  utterance.rate = 0.86
  const voice =
    synth.getVoices().find((item) => item.lang.toLowerCase().startsWith("en-us")) ??
    synth.getVoices().find((item) => item.lang.toLowerCase().startsWith("en"))
  if (voice) utterance.voice = voice
  speakTimer = window.setTimeout(() => {
    synth.resume()
    synth.speak(utterance)
  }, 60)
  return true
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
