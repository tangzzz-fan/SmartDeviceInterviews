import type { ReactNode } from 'react'
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { MermaidBlock } from './MermaidBlock'
import './markdown.css'

type Props = {
  markdown: string
  className?: string
}

function codeText(node: ReactNode): string {
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(codeText).join('')
  if (node && typeof node === 'object' && 'props' in node) {
    return codeText((node as { props?: { children?: ReactNode } }).props?.children)
  }
  return ''
}

export function MarkdownView({ markdown, className }: Props) {
  const components: Components = {
    a({ href, children }) {
      return (
        <a href={href} target="_blank" rel="noreferrer">
          {children}
        </a>
      )
    },
    pre({ children }) {
      const child = Array.isArray(children) ? children[0] : children
      const classNameAttr =
        child && typeof child === 'object' && 'props' in child
          ? String((child as { props?: { className?: string } }).props?.className ?? '')
          : ''
      const text = codeText(children).replace(/\n$/, '')
      if (classNameAttr.includes('language-mermaid')) {
        return <MermaidBlock chart={text} />
      }
      return <pre>{children}</pre>
    },
  }

  return (
    <div className={className ? `md-view ${className}` : 'md-view'}>
      <Markdown remarkPlugins={[remarkGfm]} components={components}>
        {markdown}
      </Markdown>
    </div>
  )
}
