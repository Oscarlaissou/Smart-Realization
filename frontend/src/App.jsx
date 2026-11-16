import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import Connexion from './features/auth/Connexion.jsx'
import Inscription from './features/auth/Inscription.jsx'
import Dashboard from './features/dashboard/Dashboard.jsx'
import Parcelles from './features/parcelles/Parcelles.jsx'
import Equipements from './features/equipements/Equipements.jsx'
import Humidite from './features/humidite/Humidite.jsx'
import Fertilisation from './features/fertilisation/Fertilisation.jsx'
import Camera from './features/camera/Camera.jsx'
import Alertes from './features/alertes/Alertes.jsx'
import t from './i18n/fr.js'

const liens = [['/', t.dashboard], ['/parcelles', t.parcelles], ['/equipements', t.equipements],
  ['/humidite', t.humidite], ['/fertilisation', t.fertilisation], ['/camera', t.camera], ['/alertes', t.alertes]]

function Espace({ children }) {
  if (!localStorage.getItem('token')) return <Navigate to="/connexion" />
  return (<div className="layout"><nav>{liens.map(([to, nom]) =>
    <NavLink key={to} to={to} end={to === '/'}>{nom}</NavLink>)}</nav><main>{children}</main></div>)
}

export default function App() {
  return (<Routes>
    <Route path="/connexion" element={<Connexion />} />
    <Route path="/inscription" element={<Inscription />} />
    <Route path="/" element={<Espace><Dashboard /></Espace>} />
    <Route path="/parcelles" element={<Espace><Parcelles /></Espace>} />
    <Route path="/equipements" element={<Espace><Equipements /></Espace>} />
    <Route path="/humidite" element={<Espace><Humidite /></Espace>} />
    <Route path="/fertilisation" element={<Espace><Fertilisation /></Espace>} />
    <Route path="/camera" element={<Espace><Camera /></Espace>} />
    <Route path="/alertes" element={<Espace><Alertes /></Espace>} />
  </Routes>)
}
