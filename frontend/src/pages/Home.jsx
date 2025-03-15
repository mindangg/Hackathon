import React from 'react'

import logo from '../assets/healthshark.jpg'

import '../styles/Home.css'

export default function Home() {
    return (
    <div>
        <div className='home'>
            <img src={logo} alt='HealthShark-logo' />
            <h1>WELCOME TO HEALTHSHARK</h1>
            <p>
            In today's fast-paced world, health has become a top priority.
            HealthShark was created with the mission of providing a comprehensive
            healthcare platform, making it easier for users to access accurate
            medical information, high-quality healthcare services, and effective
            tools to improve their well-being.
            </p>
        </div>
        <div id='button'>
            <a className='nav-1' href=''>Start Assessment</a>
            <a className='nav-2' href=''>Start Your Health Chat Today</a>
        </div>
        </div>
    )
}
