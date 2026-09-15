import { Link, useLocation } from 'react-router-dom'
import './consola.css'

/** Shell de la consola del coach: barra lateral fija + contenido. */
export default function Consola({ coach, children }) {
  const { pathname } = useLocation()

  return (
    <div className="consola atv-shell">
      <aside className="consola-side">
        <Link to="/" className="consola-brand">
          <span className="sq">R</span>
          <strong>ROADMAPS</strong>
        </Link>
        <nav className="consola-nav">
          <Link to="/" className={pathname === '/' ? 'on' : ''}>
            Roadmaps
          </Link>
          <Link to="/nuevo" className={pathname.startsWith('/nuevo') ? 'on' : ''}>
            Nuevo
          </Link>
        </nav>
        <div className="consola-foot">
          <span className="avatar">{(coach || '?').slice(0, 2).toUpperCase()}</span>
          <div>
            <div className="n">{coach || '—'}</div>
            <div className="r">Coach</div>
          </div>
        </div>
      </aside>
      <main className="consola-main">{children}</main>
    </div>
  )
}
