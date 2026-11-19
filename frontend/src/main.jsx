import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './i18n/index.js'
import './index.css'

function contrasteEnregistre() {
  try {
    return JSON.parse(localStorage.getItem('sevia_contraste_eleve')) === true
  } catch {
    return false
  }
}

document.documentElement.dataset.contraste = contrasteEnregistre() ? 'eleve' : 'normal'

createRoot(document.getElementById('root')).render(<BrowserRouter><App /></BrowserRouter>)
