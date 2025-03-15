import React, { useState } from 'react'
import { Link } from 'react-router-dom'

// import { useLogin } from '../hooks/useLogin'

import '../styles/Login.css'

export default function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')

    // const { login, error, isLoading } = useLogin()

    const handleSubmit = async (e) => {
        e.preventDefault()

        // await login(username, password)
    }

    return (
        <form className='login-page' onSubmit={handleSubmit}>
            <h1>Login</h1>

            <div className='login-input'>
                <input type='text' placeholder='Username' value={username} 
                        onChange={(e) => setUsername(e.target.value)}></input>
            </div>

            <div className='login-input'>
                <input type='password' placeholder='Password' value={password}
                        onChange={(e) => setPassword(e.target.value)}></input>
            </div>
            <button type='submit'>Login</button>

            <div className='login-signup'>
                <Link to='/signup'>Sign Up</Link>
            </div>
            
        </form>
    )
}
