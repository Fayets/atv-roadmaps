import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Consola from '../components/Consola.jsx'
import { ESTADOS, desdeAhora, eliminarRoadmap, listarRoadmaps, sesion } from '../api.js'
import './consola-page.css'

export default function ConsolaPage() {
  const navegar = useNavigate()
  const [coach, setCoach] = useState('')
  const [roadmaps, setRoadmaps] = useState(null)
  const [busqueda, setBusqueda] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    sesion()
      .then((s) => setCoach(s.coach))
      .catch(() => setError('Iniciá sesión en atvos.io para entrar.'))
    listarRoadmaps()
      .then(setRoadmaps)
      .catch((e) => setError(e.message))
  }, [])

  const visibles = useMemo(() => {
    const texto = busqueda.trim().toLowerCase()
    if (!texto) return roadmaps || []
    return (roadmaps || []).filter((r) =>
      `${r.cliente_nombre} ${r.canal} ${r.programa || ''} ${r.titulo || ''}`
        .toLowerCase()
        .includes(texto),
    )
  }, [roadmaps, busqueda])

  return (
    <Consola coach={coach}>
      {error && <div className="error-box">{error}</div>}

      {roadmaps !== null && roadmaps.length > 0 && (
        <input
          id="buscar-roadmap"
          className="buscador"
          type="search"
          placeholder="Buscar por cliente, canal o programa…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
      )}

      {roadmaps === null && <p className="cargando">Cargando roadmaps…</p>}

      {roadmaps?.length === 0 && (
        <p className="vacio">Todavía no generaste ninguno. Empezá por «Nuevo», en la barra de la izquierda.</p>
      )}

      {roadmaps !== null && roadmaps.length > 0 && visibles.length === 0 && (
        <p className="vacio">Ningún roadmap con ese nombre.</p>
      )}

      {visibles.length > 0 && (
        <div className="docs">
          {visibles.map((r) => (
            <Documento
              key={r.token}
              roadmap={r}
              onAbrir={() => navegar(`/r/${r.token}`)}
              onEliminar={() =>
                setRoadmaps((prev) => prev.filter((x) => x.token !== r.token))
              }
            />
          ))}
        </div>
      )}
    </Consola>
  )
}

function Documento({ roadmap, onAbrir, onEliminar }) {
  const estado = ESTADOS[roadmap.estado] || { label: roadmap.estado, clase: '' }
  const [menu, setMenu] = useState(false)
  const [copiado, setCopiado] = useState(false)
  // Borrar no se deshace, así que el menú pide confirmación en el lugar en vez
  // de abrir un diálogo del navegador.
  const [confirmando, setConfirmando] = useState(false)
  const [borrando, setBorrando] = useState(false)
  const caja = useRef(null)

  // Un menú abierto que no se cierra al hacer clic afuera es una molestia.
  useEffect(() => {
    if (!menu) return undefined
    const cerrar = (e) => {
      if (!caja.current?.contains(e.target)) {
        setMenu(false)
        setConfirmando(false)
      }
    }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [menu])

  async function copiarLink() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/f/${roadmap.token}`)
      setCopiado(true)
      setTimeout(() => {
        setCopiado(false)
        setMenu(false)
      }, 1200)
    } catch {
      setMenu(false)
    }
  }

  async function borrar() {
    setBorrando(true)
    try {
      await eliminarRoadmap(roadmap.token)
      onEliminar()
    } catch {
      setBorrando(false)
      setConfirmando(false)
    }
  }

  const vacio = roadmap.preview.length === 0

  return (
    <div className="doc-card" ref={caja}>
      <button type="button" className="doc-hoja" onClick={onAbrir} aria-label={`Abrir ${roadmap.cliente_nombre}`}>
        {vacio ? (
          <span className="doc-hoja-vacia">{estado.label}</span>
        ) : (
          <span className="mini" aria-hidden="true">
            <b>{roadmap.titulo || 'Próximos pasos'}</b>
            {roadmap.preview.map((linea, i) => (
              <i key={i}>{linea}</i>
            ))}
          </span>
        )}
      </button>

      <div className="doc-pie">
        <span className="doc-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
            <path d="M14 3v5h5" />
          </svg>
        </span>
        <span className="doc-datos">
          <b>{roadmap.cliente_nombre}</b>
          <small>
            <span className={`punto ${estado.clase}`} /> {estado.label} · {desdeAhora(roadmap.actualizado_en)}
          </small>
        </span>
        <button
          type="button"
          className="doc-menu"
          aria-label="Más acciones"
          aria-expanded={menu}
          onClick={() => setMenu((v) => !v)}
        >
          ⋮
        </button>

        {menu && (
          <div className="doc-menu-caja" role="menu">
            <button type="button" onClick={onAbrir}>
              Abrir
            </button>
            <button type="button" onClick={copiarLink}>
              {copiado ? 'Link copiado' : 'Copiar link del formulario'}
            </button>
            {confirmando ? (
              <button type="button" className="peligro" disabled={borrando} onClick={borrar}>
                {borrando ? 'Eliminando…' : '¿Seguro? Eliminar'}
              </button>
            ) : (
              <button type="button" className="peligro" onClick={() => setConfirmando(true)}>
                Eliminar
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
