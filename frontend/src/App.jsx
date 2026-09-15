import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import ConsolaPage from './pages/ConsolaPage.jsx'
import NuevoPage from './pages/NuevoPage.jsx'
import FormularioPage from './pages/FormularioPage.jsx'
import RoadmapPage from './pages/RoadmapPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Consola del coach: entra con la cookie del ecosistema. */}
        <Route path="/" element={<ConsolaPage />} />
        <Route path="/nuevo" element={<NuevoPage />} />
        {/* Público: el cliente entra con el token del link. */}
        <Route path="/f/:token" element={<FormularioPage />} />
        <Route path="/r/:token" element={<RoadmapPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
