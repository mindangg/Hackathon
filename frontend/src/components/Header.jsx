import React from 'react'

import '../styles/Header.css'

export default function Header() {
    return (
        <header id='header'>
            <div className='nav-bar'>
                <div className='Text-icon'>
                    <a href='#'>HealthShark</a>
                </div>
                <div className='attribute-nav-bar'>
                    <a href='#'>HOME</a>
                    <a href='#'>HEALTHSHARK SERVICES</a>
                </div>
            </div>
        </header>
    )
}
