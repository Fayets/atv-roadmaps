import { useEffect, useMemo, useState } from 'react'
import Consola from '../components/Consola.jsx'
import { crearRoadmap, desdeAhora, listarCanales, sesion } from '../api.js'
import './nuevo-page.css'

export default function NuevoPage() {
  const [coach, setCoach] = useState('')
  const [datos, setDatos] = useState(null)
  const [categoria, setCategoria] = useState('todos')
  const [busqueda, setBusqueda] = useState('')
  const [elegido, setElegido] = useState(null)
  const [llamada, setLlamada] = useState('')
  const [creando, setCreando] = useState(false)
  const [creado, setCreado] = useState(null)
  const [copiado, setCopiado] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    sesion()
      .then((s) => setCoach(s.coach))
      .catch(() => {})
    listarCanales()
      .then(setDatos)
      .catch((e) => setError(e.message))
  }, [])

  const visibles = useMemo(() => {
    const canales = datos?.canales || []
    const texto = busqueda.trim().toLowerCase()
    return canales.filter((c) => {
      if (categoria !== 'todos' && (c.categoria || 'sin categoría') !== categoria) return false
      if (!texto) return true
      return `${c.canal} ${c.cliente_nombre || ''}`.toLowerCase().includes(texto)
    })
  }, [datos, categoria, busqueda])

  async function crear() {
    if (!elegido) return
    setCreando(true)
    setError('')
    try {
      setCreado(
        await crearRoadmap({
          canal: elegido.canal,
          categoria: elegido.categoria,
          cliente_nombre: elegido.cliente_nombre,
          cliente_id: elegido.cliente_id,
          programa: elegido.programa,
          llamada_url: llamada.trim(),
        }),
      )
    } catch (e) {
      setError(e.message)
    } finally {
      setCreando(false)
    }
  }

  async function copiar(texto, cual) {
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado(cual)
      setTimeout(() => setCopiado(''), 2000)
    } catch {
      setError('No se pudo copiar. Seleccioná el link y copialo a mano.')
    }
  }

  if (creado) {
    const mensaje = `Hola ${creado.cliente_nombre}, te dejo el formulario para armar tu roadmap de los próximos 90 días. Son 10 minutos: ${creado.link}`
    return (
      <Consola coach={coach}>
        <div className="consola-head">
          <div>
            <h1>Link creado</h1>
            <div className="sub">
              #{creado.canal} · vence el {new Date(creado.vence_en).toLocaleDateString('es-AR')}
            </div>
          </div>
        </div>
        <div className="linkcard shell-card">
          <h2>Formulario de roadmap · {creado.cliente_nombre}</h2>
          <div className="linkrow">
            <div className="linkbox">{creado.link}</div>
            <button type="button" className="btn btn-primary" onClick={() => copiar(creado.link, 'link')}>
              {copiado === 'link' ? 'Copiado' : 'Copiar link'}
            </button>
          </div>
          <div className="sendrow">
            <button type="button" className="btn" onClick={() => copiar(mensaje, 'mensaje')}>
              {copiado === 'mensaje' ? 'Copiado' : 'Copiar mensaje para Discord'}
            </button>
            <a className="btn" href={creado.link} target="_blank" rel="noreferrer">
              Vista previa del formulario
            </a>
          </div>
          <p className="dim nota">
            Cuando el cliente lo complete, el roadmap aparece en la lista sin que nadie avise.
          </p>
        </div>
      </Consola>
    )
  }

  return (
    <Consola coach={coach}>
      <div className="consola-head">
        <div>
          <h1>Nuevo roadmap</h1>
          <div className="sub">Elegí el canal del cliente. La lista viene de ATV Clients.</div>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}
      {datos === null && !error && <p className="cargando">Cargando canales…</p>}

      {datos && (
        <div className="picker shell-card">
          <div className="cats">
            <div className="lbl">Categoría</div>
            <button
              type="button"
              className={categoria === 'todos' ? 'on' : ''}
              onClick={() => setCategoria('todos')}
            >
              Todos <span className="c">{datos.canales.length}</span>
            </button>
            {datos.categorias.map((c) => (
              <button
                key={c.id}
                type="button"
                className={categoria === c.id ? 'on' : ''}
                onClick={() => setCategoria(c.id)}
              >
                {c.label} <span className="c">{c.cantidad}</span>
              </button>
            ))}
          </div>

          <div className="picker-body">
            <input
              id="buscar-canal"
              className="search"
              type="search"
              placeholder="Buscar canal o cliente…"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />

            <div className="chan-list">
              {visibles.length === 0 && <p className="vacio">Ningún canal con ese nombre.</p>}
              {visibles.map((c) => (
                <button
                  type="button"
                  key={c.canal}
                  className={`chan ${elegido?.canal === c.canal ? 'sel' : ''}`}
                  onClick={() => setElegido(c)}
                >
                  <span className="hash">#</span>
                  <span className="who">
                    <b>{c.canal}</b>
                    <small>
                      {c.cliente_nombre}
                      {c.categoria ? ` · ${c.categoria}` : ''}
                    </small>
                  </span>
                  <span className="meta">
                    {c.tiene_roadmap ? 'Ya tiene roadmap' : desdeAhora(c.ultima_actividad)}
                  </span>
                </button>
              ))}
            </div>

            <label className="llamada" htmlFor="llamada-url">
              <span>
                Link de la llamada <i>(opcional)</i>
              </span>
              <input
                id="llamada-url"
                className="search"
                type="url"
                placeholder="https://fathom.video/share/…"
                value={llamada}
                onChange={(e) => setLlamada(e.target.value)}
              />
            </label>

            <div className="picker-foot">
              <span className="dim">
                {elegido ? (
                  <>
                    Seleccionado: <b>#{elegido.canal}</b>
                  </>
                ) : (
                  'Ningún canal seleccionado'
                )}
              </span>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!elegido || creando}
                onClick={crear}
              >
                {creando ? 'Creando…' : 'Crear link del formulario'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Consola>
  )
}
