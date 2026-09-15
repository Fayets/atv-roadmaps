import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { enviarFormulario, verFormulario } from '../api.js'
import './cliente.css'

export default function FormularioPage() {
  const { token } = useParams()
  const [form, setForm] = useState(null)
  const [paso, setPaso] = useState(0)
  const [respuestas, setRespuestas] = useState({})
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const [listo, setListo] = useState(false)

  useEffect(() => {
    verFormulario(token)
      .then((f) => {
        setForm(f)
        setRespuestas(f.respuestas || {})
        if (f.estado !== 'link_enviado') setListo(true)
      })
      .catch((e) => setError(e.message))
  }, [token])

  if (error && !form) {
    return (
      <div className="atv-shell cliente-page">
        <div className="cliente-card shell-card">
          <div className="cliente-body">
            <h1>No pudimos abrir tu formulario</h1>
            <p className="cliente-lede">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!form) return <div className="atv-shell cliente-page"><p className="cliente-cargando">Cargando…</p></div>

  if (listo) {
    return (
      <div className="atv-shell cliente-page">
        <div className="cliente-card shell-card">
          <div className="cliente-body cliente-gracias">
            <span className="tilde" aria-hidden="true">✓</span>
            <h1>Listo, {form.cliente_nombre.split(' ')[0]}</h1>
            <p className="cliente-lede">
              Ya tenemos tus respuestas. Tu coach va a repasar tus próximos pasos y te los comparte por
              el canal de siempre.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const bloque = form.bloques[paso]
  const ultimo = paso === form.bloques.length - 1
  const faltan = bloque.preguntas.filter((p) => p.requerida !== false && vacia(respuestas[p.id]))

  function responder(id, valor) {
    setRespuestas((prev) => ({ ...prev, [id]: valor }))
  }

  function alternar(id, opcionId) {
    const actuales = Array.isArray(respuestas[id]) ? respuestas[id] : []
    responder(
      id,
      actuales.includes(opcionId) ? actuales.filter((o) => o !== opcionId) : [...actuales, opcionId],
    )
  }

  async function avanzar() {
    setError('')
    if (faltan.length) {
      setError(`Te falta responder: ${faltan.map((p) => p.label).join(', ')}`)
      return
    }
    if (!ultimo) {
      setPaso(paso + 1)
      window.scrollTo({ top: 0 })
      return
    }
    setEnviando(true)
    try {
      await enviarFormulario(token, respuestas)
      setListo(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="atv-shell cliente-page">
      <div className="cliente-card shell-card">
        <header className="cliente-head">
          <div className="brandline">
            <span className="lg">
              <img src="/ATVWhite.png" alt="" />
              <strong>Aumenta Tu Valor</strong>
            </span>
            {form.programa && <span className="tag red">{form.programa}</span>}
          </div>
          <h1>Tus próximos pasos del mes</h1>
          <p className="cliente-lede">
            Siete preguntas y tu coach arma el plan de las próximas cuatro semanas sobre tu negocio
            real, no sobre un promedio.
          </p>
          <div className="prog" aria-hidden="true">
            {form.bloques.map((b, i) => (
              <i key={b.id} className={i < paso ? 'done' : i === paso ? 'now' : ''} />
            ))}
          </div>
          <div className="stepline">
            <span>
              Paso {paso + 1} de {form.bloques.length}
            </span>
            <b>{bloque.titulo}</b>
          </div>
        </header>

        <div className="cliente-body">
          {bloque.preguntas.map((p) => (
            <div className="q" key={p.id}>
              <label htmlFor={`q-${p.id}`}>{p.label}</label>
              {p.ayuda && <span className="help">{p.ayuda}</span>}
              <Campo
                pregunta={p}
                valor={respuestas[p.id]}
                onTexto={(v) => responder(p.id, v)}
                onOpcion={(v) => responder(p.id, v)}
                onAlternar={(v) => alternar(p.id, v)}
              />
            </div>
          ))}

          {error && <div className="cliente-error">{error}</div>}

          <div className="cliente-foot">
            <span className="nota">Tus respuestas las ve tu coach y nadie más.</span>
            <div className="cliente-acciones">
              {paso > 0 && (
                <button type="button" className="btn-cliente-sec" onClick={() => setPaso(paso - 1)}>
                  Volver
                </button>
              )}
              <button type="button" className="btn-cliente" onClick={avanzar} disabled={enviando}>
                {enviando ? 'Enviando…' : ultimo ? 'Enviar' : 'Continuar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Campo({ pregunta, valor, onTexto, onOpcion, onAlternar }) {
  const id = `q-${pregunta.id}`

  if (pregunta.tipo === 'texto_largo') {
    return (
      <textarea
        id={id}
        className="field ta"
        rows={3}
        value={valor || ''}
        onChange={(e) => onTexto(e.target.value)}
      />
    )
  }

  if (pregunta.tipo === 'numero') {
    return (
      <input
        id={id}
        className="field"
        type="number"
        inputMode="numeric"
        value={valor ?? ''}
        onChange={(e) => onTexto(e.target.value === '' ? '' : Number(e.target.value))}
      />
    )
  }

  if (pregunta.tipo === 'opcion') {
    return (
      <div className="chips" id={id}>
        {pregunta.opciones.map((o) => (
          <button
            type="button"
            key={o.id}
            className={`chip ${valor === o.id ? 'on' : ''}`}
            onClick={() => onOpcion(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
    )
  }

  if (pregunta.tipo === 'opciones') {
    const marcadas = Array.isArray(valor) ? valor : []
    return (
      <div className="chips" id={id}>
        {pregunta.opciones.map((o) => (
          <button
            type="button"
            key={o.id}
            className={`chip ${marcadas.includes(o.id) ? 'on' : ''}`}
            onClick={() => onAlternar(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
    )
  }

  return (
    <input id={id} className="field" type="text" value={valor || ''} onChange={(e) => onTexto(e.target.value)} />
  )
}

function vacia(valor) {
  if (valor === null || valor === undefined) return true
  if (typeof valor === 'string') return valor.trim() === ''
  if (Array.isArray(valor)) return valor.length === 0
  return false
}
