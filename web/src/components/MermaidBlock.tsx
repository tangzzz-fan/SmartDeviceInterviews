import { useEffect, useId, useRef } from 'react'
import mermaid from 'mermaid'

mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  fontFamily: 'SF Pro Text, PingFang SC, system-ui, sans-serif',
})

export function MermaidBlock({ chart }: { chart: string }) {
  const id = useId().replace(/:/g, '')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let gone = false
    const render = async () => {
      const renderId = `mmd-${id}-${Math.random().toString(36).slice(2, 9)}`
      try {
        const { svg } = await mermaid.render(renderId, chart)
        if (!gone && ref.current) ref.current.innerHTML = svg
      } catch (err) {
        if (!gone && ref.current) {
          ref.current.innerHTML = ''
          ref.current.textContent = `Mermaid 渲染失败：${String(err)}`
        }
      }
    }
    void render()
    return () => {
      gone = true
    }
  }, [chart, id])

  return <div className="mermaid-box" ref={ref} />
}
