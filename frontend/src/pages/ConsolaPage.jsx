import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Consola from '../components/Consola.jsx'
import { ESTADOS, desdeAhora, listarRoadmaps, sesion } from '../api.js'
import './consola-page.css'

export default function ConsolaPage() {
  const navegar = useNavigate()
  const [coach, setCoach] = useState('')
  const [roadmaps, setRoadmaps] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    sesion()
      .then((s) => setCoach(s.coach))
      .catch(() => setError('Iniciá sesión en atvos.io para entrar.'))
    listarRoadmaps()
      .then(setRoadmaps)
      .catch((e) => setError(e.message))
  }, [])

  const esperando = (roadmaps || []).filter((r) => r.estado === 'link_enviado').length
  const porRevisar = (roadmaps || []).filter((r) => r.estado === 'listo_para_revisar').length

  return (
    <Consola coach={coach}>
      <div className="consola-head">
        <div>
          <h1>Roadmaps</h1>
          <div className="sub">
            {roadmaps === null
              ? 'Cargando…'
              : `${esperando} esperando formulario · ${porRevisar} listo${porRevisar === 1 ? '' : 's'} para revisar`}
          </div>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      <button type="button" className="btn-hero" onClick={() => navegar('/nuevo')}>
        <span className="plus" aria-hidden="true">
          +
        </span>
        <span>
          Generar nuevo roadmap a cliente
          <small>Elegís el canal, se crea el link y se lo mandás</small>
        </span>
      </button>

      {roadmaps === null && <p className="cargando">Cargando roadmaps…</p>}

      {roadmaps?.length === 0 && (
        <p className="vacio">Todavía no generaste ninguno. Empezá por el botón de arriba.</p>
      )}

      {roadmaps?.length > 0 && (
        <div className="shell-card tabla-card">
          <div className="tabla-wrap">
          <table className="tabla">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Programa</th>
                <th>Estado</th>
                <th>Avance</th>
                <th>Actualizado</th>
              </tr>
            </thead>
            <tbody>
              {roadmaps.map((r) => {
                const estado = ESTADOS[r.estado] || { label: r.estado, clase: '' }
                return (
                  <tr key={r.token}>
                    <td>
                      <Link to={`/r/${r.token}`} className="cli">
                        <span className="av">{iniciales(r.cliente_nombre)}</span>
                        <span>
                          <span className="nm">{r.cliente_nombre}</span>
                          <span className="ch">#{r.canal}</span>
                        </span>
                      </Link>
                    </td>
                    <td className="muted">{r.programa || '—'}</td>
                    <td>
                      <span className={`pill ${estado.clase}`}>{estado.label}</span>
                    </td>
                    <td className="dim num">
                      {r.tareas_totales ? `${r.tareas_hechas}/${r.tareas_totales}` : '—'}
                    </td>
                    <td className="dim num">{desdeAhora(r.actualizado_en)}</td>
                  </tr>
                )
              })}
            </tbody>
            </table>
          </div>
        </div>
      )}
    </Consola>
  )
}

function iniciales(nombre) {
  return (nombre || '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
}
