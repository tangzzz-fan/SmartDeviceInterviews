import { useEffect, useId, useRef, useState } from 'react'
import SpeechRecognition, {
  useSpeechRecognition,
} from 'react-speech-recognition'
import './SpeechTextarea.css'

type Props = {
  value: string
  onChange: (next: string) => void
  rows?: number
  placeholder?: string
  disabled?: boolean
  /** BCP-47, default zh-CN for interview drills */
  language?: string
  className?: string
}

/** Which SpeechTextarea instance currently owns the mic (singleton Web Speech API). */
let activeOwnerId: string | null = null
const ownerListeners = new Set<() => void>()

function setActiveOwner(id: string | null) {
  activeOwnerId = id
  for (const notify of ownerListeners) notify()
}

/**
 * Textarea with optional mic dictation via react-speech-recognition.
 * Appends speech to the current value; typing remains fully editable.
 */
export function SpeechTextarea({
  value,
  onChange,
  rows = 4,
  placeholder,
  disabled = false,
  language = 'zh-CN',
  className = '',
}: Props) {
  const ownerId = useId()
  const [, bump] = useState(0)
  const prefixRef = useRef('')
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
    browserSupportsContinuousListening,
    isMicrophoneAvailable,
  } = useSpeechRecognition({ clearTranscriptOnListen: true })

  const isOwner = activeOwnerId === ownerId
  const isListeningHere = listening && isOwner

  useEffect(() => {
    const notify = () => bump((n) => n + 1)
    ownerListeners.add(notify)
    return () => {
      ownerListeners.delete(notify)
      if (activeOwnerId === ownerId) {
        void SpeechRecognition.abortListening()
        setActiveOwner(null)
      }
    }
  }, [ownerId])

  useEffect(() => {
    if (!isOwner || !listening) return
    const spoken = transcript.trim()
    if (!spoken) return
    const base = prefixRef.current
    onChange(base ? `${base.replace(/\s+$/, '')} ${spoken}` : spoken)
  }, [transcript, isOwner, listening, onChange])

  async function toggleMic() {
    if (disabled) return
    if (isListeningHere) {
      await SpeechRecognition.stopListening()
      setActiveOwner(null)
      return
    }
    if (listening) {
      await SpeechRecognition.abortListening()
    }
    prefixRef.current = value
    resetTranscript()
    setActiveOwner(ownerId)
    await SpeechRecognition.startListening({
      continuous: browserSupportsContinuousListening,
      language,
    })
  }

  return (
    <div className={`speech-field ${className}`.trim()}>
      <textarea
        rows={rows}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="speech-toolbar">
        {!browserSupportsSpeechRecognition ? (
          <span className="speech-hint muted">
            当前浏览器不支持语音识别（建议 Chrome / Edge）
          </span>
        ) : (
          <>
            <button
              type="button"
              className={`speech-mic ${isListeningHere ? 'listening' : ''}`}
              disabled={disabled || !isMicrophoneAvailable}
              onClick={() => void toggleMic()}
              aria-pressed={isListeningHere}
              title={isListeningHere ? '停止录音' : '语音输入'}
            >
              {isListeningHere ? '● 录音中…点击停止' : '🎤 语音输入'}
            </button>
            {isListeningHere && (
              <span className="speech-hint listening-hint">
                识别中（{language}）· 可边说边改文字
              </span>
            )}
            {!isMicrophoneAvailable && (
              <span className="speech-hint muted">请允许麦克风权限</span>
            )}
          </>
        )}
      </div>
    </div>
  )
}
