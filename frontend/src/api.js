/**
 * Única frontera con el backend. Ningún componente hace fetch por su cuenta:
 * si cambia una ruta, se cambia acá y nada más se entera.
 */

const BASE = import.meta.env.VITE_API_URL || ''

async function pedir(ruta, opciones = {}) {
  const respuesta = await fetch(`${BASE}/api${ruta}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...opciones,
  })

  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`
    try {
      const cuerpo = await respuesta.json()
      if (cuerpo?.detail) detalle = cuerpo.detail
    } catch {
      /* el backend no siempre responde JSON (502, timeouts del proxy) */
    }
    const error = new Error(detalle)
    error.status = respuesta.status
    throw error
  }

  return respuesta.status === 204 ? null : respuesta.json()
}

// ——— consola del coach ———
export const sesion = () => pedir('/auth/session')
export const listarCanales = () => pedir('/canales/')
export const listarRoadmaps = () => pedir('/roadmaps/')
export const crearRoadmap = (datos) =>
  pedir('/roadmaps/', { method: 'POST', body: JSON.stringify(datos) })
export const verRoadmap = (token) => pedir(`/roadmaps/${token}`)
export const entregarRoadmap = (token) => pedir(`/roadmaps/${token}/entregar`, { method: 'POST' })
export const eliminarRoadmap = (token) => pedir(`/roadmaps/${token}`, { method: 'DELETE' })
export const regenerar = (token) => pedir(`/ia/${token}/generar`, { method: 'POST' })
export const estadoGeneracion = (token) => pedir(`/ia/${token}/estado`)

// ——— público (el cliente, con el token del link) ———
export const verFormulario = (token) => pedir(`/f/${token}`)
export const enviarFormulario = (token, respuestas) =>
  pedir(`/f/${token}`, { method: 'POST', body: JSON.stringify({ respuestas }) })
export const verRoadmapPublico = (token) => pedir(`/f/${token}/roadmap`)
export const marcarTarea = (token, tareaId, hecha) =>
  pedir(`/f/${token}/roadmap/tareas/${tareaId}`, {
    method: 'POST',
    body: JSON.stringify({ hecha }),
  })

/** Etiquetas de estado: el backend manda la llave, la pantalla el texto. */
export const ESTADOS = {
  link_enviado: { label: 'Link enviado', clase: 'pill--warn' },
  formulario_completado: { label: 'Formulario completado', clase: 'pill--info' },
  generando: { label: 'Generando…', clase: 'pill--info' },
  listo_para_revisar: { label: 'Listo para revisar', clase: 'pill--brand' },
  entregado: { label: 'Entregado', clase: 'pill--ok' },
  error: { label: 'Falló la generación', clase: 'pill--brand' },
}

export function desdeAhora(iso) {
  if (!iso) return '—'
  const minutos = Math.round((Date.now() - new Date(iso + (iso.endsWith('Z') ? '' : 'Z'))) / 60000)
  if (minutos < 1) return 'recién'
  if (minutos < 60) return `hace ${minutos} min`
  const horas = Math.round(minutos / 60)
  if (horas < 24) return `hace ${horas} h`
  return `hace ${Math.round(horas / 24)} d`
}
