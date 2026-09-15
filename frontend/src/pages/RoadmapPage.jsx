import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import CampoEditable from '../components/CampoEditable.jsx'
import {
  entregarRoadmap,
  guardarRoadmap,
  marcarTarea,
  sesion,
  verRoadmapPublico,
} from '../api.js'
import './cliente.css'
import './roadmap-page.css'

/** Estados en los que todavía no hay nada que mostrar: se reintenta solo. */
const EN_CURSO = ['link_enviado', 'formulario_completado', 'generando']

export default function RoadmapPage() {
  const { token } = useParams()
  const [roadmap, setRoadmap] = useState(null)
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(null)
  // Solo el coach edita. El cliente abre el mismo link y no ve ningún control.
  const [esCoach, setEsCoach] = useState(false)
  const [borrador, setBorrador] = useState(null)
  const [salvando, setSalvando] = useState(false)
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
    sesion()
      .then(() => setEsCoach(true))
      .catch(() => setEsCoach(false))
  }, [cargar])

  // Mientras la IA trabaja, la página se actualiza sola: nadie tiene que recargar.
  useEffect(() => {
    if (!roadmap || borrador || !EN_CURSO.includes(roadmap.estado)) return undefined
    temporizador.current = setTimeout(cargar, 5000)
    return () => clearTimeout(temporizador.current)
  }, [roadmap, borrador, cargar])

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

  async function guardar() {
    setSalvando(true)
    setError('')
    try {
      setRoadmap(await guardarRoadmap(token, limpiar(borrador)))
      setBorrador(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setSalvando(false)
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

  const editando = borrador !== null
  const doc = editando ? borrador : roadmap

  // Si los bloques son días (un plan corto) en vez de semanas, "del mes" y
  // "de la semana" suenan mal. Los rótulos siguen al contenido.
  const porDias = doc.semanas.some((s) => /d[ií]as?\s*\d/i.test(s.etiqueta || ''))
  const rotulos = porDias
    ? { meta: 'Meta principal', foco: 'Foco', entregables: 'Entregables' }
    : { meta: 'Meta principal del mes', foco: 'Foco del mes', entregables: 'Entregables de la semana:' }

  const cambiar = (campo) => (valor) => setBorrador((b) => ({ ...b, [campo]: valor }))

  const cambiarSemana = (i, campo) => (valor) =>
    setBorrador((b) => ({
      ...b,
      semanas: b.semanas.map((s, j) => (j === i ? { ...s, [campo]: valor } : s)),
    }))

  const cambiarLista = (i, lista, k, campo) => (valor) =>
    setBorrador((b) => ({
      ...b,
      semanas: b.semanas.map((s, j) =>
        j === i
          ? { ...s, [lista]: s[lista].map((x, l) => (l === k ? { ...x, [campo]: valor } : x)) }
          : s,
      ),
    }))

  const agregar = (i, lista, item) =>
    setBorrador((b) => ({
      ...b,
      semanas: b.semanas.map((s, j) => (j === i ? { ...s, [lista]: [...s[lista], item] } : s)),
    }))

  const quitar = (i, lista, k) =>
    setBorrador((b) => ({
      ...b,
      semanas: b.semanas.map((s, j) =>
        j === i ? { ...s, [lista]: s[lista].filter((_, l) => l !== k) } : s,
      ),
    }))

  return (
    <div className="atv-shell doc-page">
      <article className={`doc shell-card ${editando ? 'doc--editando' : ''}`}>
        <div className="doc-cover" />
        <div className="doc-inner">
          <header className="doc-head">
            {editando ? (
              <CampoEditable
                variante="e-titulo"
                valor={doc.titulo}
                onCambio={cambiar('titulo')}
                placeholder="Título del documento"
              />
            ) : (
              <h1 className="doc-titulo">{doc.titulo}</h1>
            )}
            <p className="doc-sub">
              {roadmap.cliente_nombre}
              {roadmap.mes && !porDias ? ` · ${roadmap.mes}` : ''}
              {roadmap.programa ? ` · ${roadmap.programa}` : ''}
            </p>
            {roadmap.llamada_url && !editando && (
              <p className="doc-llamada">
                Llamada{roadmap.llamada_fecha ? ` (${fecha(roadmap.llamada_fecha)})` : ''}:{' '}
                <a href={roadmap.llamada_url} target="_blank" rel="noreferrer">
                  {roadmap.llamada_url}
                </a>
              </p>
            )}
          </header>

          <div className="brief">
            <Dato k={rotulos.meta} v={doc.meta_mes} editando={editando} onCambio={cambiar('meta_mes')} />
            <Dato k={rotulos.foco} v={doc.foco_mes} editando={editando} onCambio={cambiar('foco_mes')} />
            <Dato k="Avatar" v={doc.avatar} editando={editando} onCambio={cambiar('avatar')} />
            <Dato
              k={`Cómo trabajamos${roadmap.programa ? ` (${roadmap.programa})` : ''}`}
              v={doc.como_trabajamos}
              bloque
              editando={editando}
              onCambio={cambiar('como_trabajamos')}
            />
          </div>

          {error && <div className="cliente-error avance-error">{error}</div>}

          {doc.semanas.map((semana, i) => (
            <section className="semana" key={semana.id ?? i}>
              {editando ? (
                <div className="e-semana-head">
                  <CampoEditable
                    variante="e-etiqueta"
                    valor={semana.etiqueta}
                    onCambio={cambiarSemana(i, 'etiqueta')}
                    placeholder="Semana 1"
                  />
                  <CampoEditable
                    variante="e-nombre"
                    valor={semana.nombre}
                    onCambio={cambiarSemana(i, 'nombre')}
                    placeholder="Nombre del bloque"
                  />
                  <button
                    type="button"
                    className="e-quitar"
                    aria-label="Quitar bloque"
                    onClick={() =>
                      setBorrador((b) => ({ ...b, semanas: b.semanas.filter((_, j) => j !== i) }))
                    }
                  >
                    ×
                  </button>
                </div>
              ) : (
                <h2 className="semana-titulo">
                  {semana.etiqueta}
                  {semana.nombre ? ` — ${semana.nombre}` : ''}
                </h2>
              )}

              <ul className="tareas">
                {semana.tareas.map((t, k) => (
                  <li key={t.id ?? k} className={!editando && t.hecha ? 'hecha' : undefined}>
                    {editando ? (
                      <>
                        <button
                          type="button"
                          className={`e-quien ${t.quien === 'nosotros' ? 'on' : ''}`}
                          title="Quién ejecuta esta tarea"
                          onClick={() =>
                            cambiarLista(i, 'tareas', k, 'quien')(
                              t.quien === 'nosotros' ? 'cliente' : 'nosotros',
                            )
                          }
                        >
                          {t.quien === 'nosotros' ? 'nosotros' : 'cliente'}
                        </button>
                        <CampoEditable
                          variante="e-tarea"
                          valor={t.tarea}
                          onCambio={cambiarLista(i, 'tareas', k, 'tarea')}
                          placeholder="Qué hay que hacer"
                        />
                        <button
                          type="button"
                          className="e-quitar"
                          aria-label="Quitar tarea"
                          onClick={() => quitar(i, 'tareas', k)}
                        >
                          ×
                        </button>
                      </>
                    ) : (
                      <>
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
                      </>
                    )}
                  </li>
                ))}
              </ul>

              {editando && (
                <button
                  type="button"
                  className="e-agregar"
                  onClick={() => agregar(i, 'tareas', { tarea: '', quien: 'cliente' })}
                >
                  + tarea
                </button>
              )}

              {(semana.entregables.length > 0 || editando) && (
                <div className="entregables">
                  <h3>{rotulos.entregables}</h3>
                  <ul>
                    {semana.entregables.map((e, k) => (
                      <li key={k}>
                        {editando ? (
                          <div className="e-entregable">
                            <CampoEditable
                              variante="e-linea"
                              valor={e.texto}
                              onCambio={cambiarLista(i, 'entregables', k, 'texto')}
                              placeholder="Qué queda hecho"
                            />
                            <CampoEditable
                              variante="e-linea e-url"
                              valor={e.url}
                              onCambio={cambiarLista(i, 'entregables', k, 'url')}
                              placeholder="Link (opcional)"
                            />
                            <button
                              type="button"
                              className="e-quitar"
                              aria-label="Quitar entregable"
                              onClick={() => quitar(i, 'entregables', k)}
                            >
                              ×
                            </button>
                          </div>
                        ) : e.url ? (
                          <a href={e.url} target="_blank" rel="noreferrer">
                            {e.texto}
                          </a>
                        ) : (
                          e.texto
                        )}
                      </li>
                    ))}
                  </ul>
                  {editando && (
                    <button
                      type="button"
                      className="e-agregar"
                      onClick={() => agregar(i, 'entregables', { texto: '', url: '' })}
                    >
                      + entregable
                    </button>
                  )}
                </div>
              )}
            </section>
          ))}

          {editando && (
            <button
              type="button"
              className="e-agregar e-agregar--bloque"
              onClick={() =>
                setBorrador((b) => ({
                  ...b,
                  semanas: [
                    ...b.semanas,
                    { etiqueta: `Semana ${b.semanas.length + 1}`, nombre: '', tareas: [], entregables: [] },
                  ],
                }))
              }
            >
              + bloque
            </button>
          )}

          <footer className="doc-foot">
            {!editando && (
              <span className="avance">
                <b className="num">
                  {roadmap.tareas_hechas}/{roadmap.tareas_totales}
                </b>{' '}
                tareas marcadas
              </span>
            )}

            {esCoach && (
              <div className="revision">
                {editando ? (
                  <>
                    <div>
                      <b>Estás editando el documento.</b>
                      <p>Los casilleros que el cliente ya marcó se conservan.</p>
                    </div>
                    <div className="revision-acciones">
                      <button type="button" className="btn-cliente-sec" onClick={() => setBorrador(null)}>
                        Cancelar
                      </button>
                      <button type="button" className="btn-cliente" disabled={salvando} onClick={guardar}>
                        {salvando ? 'Guardando…' : 'Guardar cambios'}
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <b>
                        {roadmap.estado === 'entregado'
                          ? 'Ya se lo entregaste al cliente.'
                          : 'Todavía no se lo mandaste al cliente.'}
                      </b>
                      <p>
                        {roadmap.estado === 'entregado'
                          ? 'Si lo corregís, el cliente ve el cambio al instante.'
                          : 'Corregí lo que haga falta y entregalo cuando esté como querés.'}
                      </p>
                    </div>
                    <div className="revision-acciones">
                      <button
                        type="button"
                        className="btn-cliente-sec"
                        onClick={() => setBorrador(copiar(roadmap))}
                      >
                        Editar
                      </button>
                      {roadmap.estado === 'listo_para_revisar' && (
                        <button type="button" className="btn-cliente" onClick={entregar}>
                          Entregar al cliente
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}
          </footer>
        </div>
      </article>
    </div>
  )
}

function Dato({ k, v, bloque, editando, onCambio }) {
  if (!editando && !v) return null
  return (
    <p className={bloque ? 'dato dato--bloque' : 'dato'}>
      <b>{k}:</b>
      {editando ? (
        <CampoEditable variante="e-dato" valor={v} onCambio={onCambio} placeholder="—" />
      ) : (
        <>
          {bloque ? <br /> : ' '}
          {v}
        </>
      )}
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

/** Copia editable del documento: solo los campos que el coach puede tocar. */
function copiar(roadmap) {
  return {
    titulo: roadmap.titulo || '',
    mes: roadmap.mes || '',
    meta_mes: roadmap.meta_mes || '',
    foco_mes: roadmap.foco_mes || '',
    avatar: roadmap.avatar || '',
    como_trabajamos: roadmap.como_trabajamos || '',
    semanas: roadmap.semanas.map((s) => ({
      id: s.id,
      etiqueta: s.etiqueta || '',
      nombre: s.nombre || '',
      tareas: s.tareas.map((t) => ({ id: t.id, tarea: t.tarea, quien: t.quien, hecha: t.hecha })),
      entregables: s.entregables.map((e) => ({ texto: e.texto, url: e.url || '' })),
    })),
  }
}

/** Fuera las filas vacías: si el coach agregó una y no la completó, no se guarda. */
function limpiar(borrador) {
  return {
    ...borrador,
    semanas: borrador.semanas
      .map((s) => ({
        etiqueta: (s.etiqueta || '').trim(),
        nombre: (s.nombre || '').trim(),
        tareas: s.tareas.filter((t) => (t.tarea || '').trim()).map((t) => ({ tarea: t.tarea.trim(), quien: t.quien })),
        entregables: s.entregables
          .filter((e) => (e.texto || '').trim())
          .map((e) => ({ texto: e.texto.trim(), url: (e.url || '').trim() || null })),
      }))
      .filter((s) => s.tareas.length || s.entregables.length),
  }
}

function fecha(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('es-AR', { day: 'numeric', month: 'long' })
}
