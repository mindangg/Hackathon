import React from 'react'

import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'

import { useAuthContext } from './hooks/useAuthContext'

import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'

import Chatbot from './components/Chatbot'
import Header from './components/Header'

import Notification from './components/Notification'

export default function App() {
  const { user } = useAuthContext()

    return (
      <div className='App'>
        <BrowserRouter>
        <Header/>
          <Routes>
            <Route path='/' element={<Home/>}/>
            <Route path='/login' element={!user ? <Login/> : <Navigate to='/'/>}/>
            <Route path='/signup' element={!user ? <Signup/> : <Navigate to='/'/>}/>
            <Route path='/chatbot' element={<Chatbot/>}/>
            {/* <Route path="/assessment" element={<Assessment />} /> */}
          </Routes>
        <Notification/>
        </BrowserRouter>
      </div>
    )
}
