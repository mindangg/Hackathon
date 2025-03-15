import React from 'react'

import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'

import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'

import Chatbot from './components/Chatbot'
import Header from './components/Header'

export default function App() {
    return (
      <div className='App'>
        <BrowserRouter>
        <Header/>
          <Routes>
            <Route path='/' element={<Home/>}/>
            <Route path='/login' element={<Login/>}/>
            <Route path='/signup' element={<Signup/>}/>
            <Route path='/chatbot' element={<Chatbot/>}/>
          </Routes>
        </BrowserRouter>
      </div>
    )
}
