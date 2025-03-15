import React from 'react'

import { Link } from 'react-router-dom'

import '../styles/Header.css'

export default function Header() {
    return (
        <header id='header'>
            <div className='nav-bar'>
                <div className='Text-icon'>
                    <Link to='/'>HealthShark</Link>
                </div>
                <div className='attribute-nav-bar'>
                    <Link to='/'>Home</Link>
                    <a href='#'>HealthShark Services</a>
                </div>
            </div>
        </header>
    )
}
