import type { ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import './layout.css'

const links = [
  { to: '/', label: '概览', end: true },
  { to: '/questions', label: '题库' },
  { to: '/practice/feynman', label: '费曼' },
  { to: '/practice/simon', label: '西蒙' },
  { to: '/practice/speak', label: '口述' },
  { to: '/columns', label: '专栏', columnNav: true },
  { to: '/checklist', label: '清单' },
  { to: '/whiteboards', label: '白板' },
  { to: '/stories', label: 'STAR' },
  { to: '/english', label: '英文' },
  { to: '/skills', label: '自评' },
  { to: '/mocks', label: '模拟面' },
]

export function Layout({ children }: { children: ReactNode }) {
  const loc = useLocation()
  const onColumn =
    loc.pathname === '/columns' || loc.pathname.startsWith('/column/')

  return (
    <div className="layout">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">SDI</span>
          <div>
            <strong>面试冲刺学习站</strong>
            <p>综合版 · 进度追踪</p>
          </div>
        </div>
        <nav>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                link.columnNav ? (onColumn ? 'active' : undefined) : isActive ? 'active' : undefined
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="content">{children}</main>
    </div>
  )
}
