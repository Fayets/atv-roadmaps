import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { entregarRoadmap, marcarTarea, verRoadmapPublico } from '../api.js'
import './cliente.css'
import './roadmap-page.css'

/** Estados en los que todavía no hay nada que mostrar: se reintenta solo. */
const EN_CURSO = ['link_enviado', 'formulario_completado', 'generando']

export default function RoadmapPage() {
  const { token } = useParams()
  const [roadmap, setRoadmap] = useState(null)
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(null)
  const temporizador = useRef(null)

  const cargar = useCallback(
    () =>
      verRoadmapPublico(token)
        .then(setRoadmap)
        .catch((e) => setError(e.message)),
    [token],
  )

  useEffect(() => {
    cargar()
  }, [cargar])

  // Mientras la IA trabaja, la página se actualiza sola: nadie tiene que recargar.
  useEffect(() => {
    if (!roadmap || !EN_CURSO.includes(roadmap.estado)) return undefined
    temporizador.current = setTimeout(cargar, 5000)
    return () => clearTimeout(temporizador.current)
  }, [roadmap, cargar])

  async function alternar(tarea) {
    setGuardando(tarea.id)
    try {
      setRoadmap(await marcarTarea(token, tarea.id, !tarea.hecha))
    } catch (e) {
      setError(e.message)
    } finally {
      setGuardando(null)
    }
  }

  async function entregar() {
    try {
      setRoadmap(await entregarRoadmap(token))
    } catch (e) {
      setError(e.message)
    }
  }

  if (error && !roadmap) return <Aviso titulo="No pudimos abrir este roadmap" texto={error} />
  if (!roadmap) {
    return (
      <div className="atv-shell cliente-page">
        <p className="cliente-cargando">Cargando…</p>
      </div>
    )
  }

  if (EN_CURSO.includes(roadmap.estado)) {
    return roadmap.estado === 'generando' ? (
      <Aviso
        titulo="Armando tus próximos pasos"
        texto="Suele tardar entre 40 segundos y 2 minutos. Esta página se actualiza sola."
      />
    ) : (
      <Aviso
        titulo="Todavía falta el formulario"
        texto="Cuando el cliente lo complete, los próximos pasos aparecen acá."
      />
    )
  }

  if (roadmap.estado === 'error') {
    return <Aviso titulo="La generación falló" texto="Se puede volver a intentar desde la consola." />
  }

  return (
    <div className="atv-shell doc-page">
      <article className="doc shell-card">
        <div className="doc-cover" />
        <div className="doc-inner">
          <header className="doc-head">
            <h1 className="doc-titulo">{roadmap.titulo}</h1>
            <p className="doc-sub">
              {roadmap.cliente_nombre}
              {roadmap.mes ? ` · ${roadmap.mes}` : ''}
              {roadmap.programa ? ` · ${roadmap.programa}` : ''}
            </p>
            {roadmap.llamada_url && (
              <p className="doc-llamada">
                Llamada{roadmap.llamada_fecha ? ` (${fecha(roadmap.llamada_fecha)})` : ''}:{' '}
                <a href={roadmap.llamada_url} target="_blank" rel="noreferrer">
                  {roadmap.llamada_url}
                </a>
              </p>
            )}
          </header>

          <div className="brief">
            <Dato k="Meta principal del mes" v={roadmap.meta_mes} />
            <Dato k="Foco del mes" v={roadmap.foco_mes} />
            <Dato k="Avatar" v={roadmap.avatar} />
            <Dato
              k={`Cómo trabajamos${roadmap.programa ? ` (${roadmap.programa})` : ''}`}
              v={roadmap.como_trabajamos}
              bloque
            />
          </div>

          {error && <div className="cliente-error avance-error">{error}</div>}

          {roadmap.semanas.map((semana, i) => (
            <section className="semana" key={semana.id ?? i}>
              <h2 className="semana-titulo">
                {semana.etiqueta}
                {semana.nombre ? ` — ${semana.nombre}` : ''}
              </h2>

              <ul className="tareas">
                {semana.tareas.map((t) => (
                  <li key={t.id} className={t.hecha ? 'hecha' : undefined}>
                    <button
                      type="button"
                      className={`box ${t.hecha ? 'on' : ''}`}
                      aria-label={t.hecha ? `Desmarcar: ${t.tarea}` : `Marcar: ${t.tarea}`}
                      aria-pressed={t.hecha}
                      disabled={guardando === t.id}
                      onClick={() => alternar(t)}
                    />
                    <span className="tarea-texto">
                      {t.tarea}
                      {t.quien === 'nosotros' && <span className="quien">nosotros hacemos</span>}
                    </span>
                  </li>
                ))}
              </ul>

              {semana.entregables.length > 0 && (
                <div className="entregables">
                  <h3>Entregables de la semana:</h3>
                  <ul>
                    {semana.entregables.map((e, j) => (
                      <li key={j}>
                        {e.url ? (
                          <a href={e.url} target="_blank" rel="noreferrer">
                            {e.texto}
                          </a>
                        ) : (
                          e.texto
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          ))}

          <footer className="doc-foot">
            <span className="avance">
              <b className="num">
                {roadmap.tareas_hechas}/{roadmap.tareas_totales}
              </b>{' '}
              tareas marcadas
            </span>
            {roadmap.estado === 'listo_para_revisar' && (
              <div className="revision">
                <div>
                  <b>Todavía no se lo mandaste al cliente.</b>
                  <p>Repasalo y entregalo cuando esté como querés.</p>
                </div>
                <button type="button" className="btn-cliente" onClick={entregar}>
                  Entregar al cliente
                </button>
              </div>
            )}
          </footer>
        </div>
      </article>
    </div>
  )
}

function Dato({ k, v, bloque }) {
  if (!v) return null
  return (
    <p className={bloque ? 'dato dato--bloque' : 'dato'}>
      <b>{k}:</b>
      {bloque ? <br /> : ' '}
      {v}
    </p>
  )
}

function Aviso({ titulo, texto }) {
  return (
    <div className="atv-shell cliente-page">
      <div className="cliente-card shell-card">
        <div className="cliente-body cliente-gracias">
          <h1>{titulo}</h1>
          <p className="cliente-lede">{texto}</p>
        </div>
      </div>
    </div>
  )
}

function fecha(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('es-AR', { day: 'numeric', month: 'long' })
}
