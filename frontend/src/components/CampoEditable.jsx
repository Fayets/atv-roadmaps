import { useEffect, useRef } from 'react'

/**
 * Un textarea que se ve como el texto que reemplaza y crece con el contenido.
 *
 * La alternativa era `contenteditable`, que da menos trabajo al principio y más
 * para siempre: pega HTML con formato, rompe el undo y obliga a limpiar lo que
 * entra. Un textarea guarda texto y nada más.
 */
export default function CampoEditable({ valor, onCambio, variante = '', placeholder, ...resto }) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [valor])

  return (
    <textarea
      ref={ref}
      className={`editable ${variante}`}
      rows={1}
      value={valor || ''}
      placeholder={placeholder}
      onChange={(e) => onCambio(e.target.value)}
      {...resto}
    />
  )
}
