import React from 'react'

import { Link } from 'react-router-dom'

import '../styles/Header.css'
import { useAuthContext } from '../hooks/useAuthContext'

import { useLogout } from '../hooks/useLogout'

export default function Header() {
    const { user } = useAuthContext()
    const { logout } = useLogout()
    return (
        <header id='header'>
            <div className='nav-bar'>
                <div className='Text-icon'>
                    <Link to='/'>HealthShark</Link>
                </div>
                <div className='attribute-nav-bar'>
                    <Link to='/'>Home</Link>
                    {!user 
                    ?(
                        <Link to='/login'>Login</Link>
                    )
                    :(
                        <Link onClick={logout}>Logout</Link>
                    )
                    }

                </div>
            </div>
        </header>
    )
}
