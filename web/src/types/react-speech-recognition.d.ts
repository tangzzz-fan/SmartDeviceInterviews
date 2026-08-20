declare module 'react-speech-recognition' {
  export type SpeechRecognitionOptions = {
    continuous?: boolean
    language?: string
  }

  export type UseSpeechRecognitionOptions = {
    transcribing?: boolean
    clearTranscriptOnListen?: boolean
    commands?: unknown[]
  }

  export type SpeechRecognitionHook = {
    transcript: string
    interimTranscript: string
    finalTranscript: string
    listening: boolean
    resetTranscript: () => void
    browserSupportsSpeechRecognition: boolean
    browserSupportsContinuousListening: boolean
    isMicrophoneAvailable: boolean
  }

  export function useSpeechRecognition(
    options?: UseSpeechRecognitionOptions,
  ): SpeechRecognitionHook

  export type SpeechRecognitionAPI = {
    startListening: (options?: SpeechRecognitionOptions) => Promise<void>
    stopListening: () => Promise<void>
    abortListening: () => Promise<void>
    getRecognition: () => unknown
  }

  const SpeechRecognition: SpeechRecognitionAPI
  export default SpeechRecognition
}
