import React, { useRef } from 'react'

import { Link } from 'react-router-dom'

import logo from '../assets/healthshark.jpg'

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faClover } from "@fortawesome/free-solid-svg-icons";
import { faCapsules } from "@fortawesome/free-solid-svg-icons";
import { faBowlFood } from "@fortawesome/free-solid-svg-icons";

import '../styles/Home.css'

export default function Home() {
    const infoRef = useRef(null);
    const serviceRef = useRef(null);
    const supportRef = useRef(null);

    const scrollToSection = (ref) => {
    if (ref.current) {
        ref.current.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
        console.log("ref.current is null");
    }
    };

    return (
        <div>
          <div className="HOME">
            <img src={logo} alt="HealthShark-logo" />
            <h1>WELCOME TO HEALTHSHARK</h1>
            <p>
              In today's fast-paced world, health has become a top priority.
              HealthShark was created with the mission of providing a comprehensive
              healthcare platform, making it easier for users to access accurate
              medical information, high-quality healthcare services, and effective
              tools to improve their well-being.
            </p>
    
            {/* Gộp button vào chung với nội dung để dễ căn chỉnh */}
            <div id="button">
              <Link to="/assessment" className="nav-1">
                Start Assessment
              </Link>
              <Link to="/chatbot" className="nav-2">
                Start Your Health Chat Today
              </Link>
            </div>
    
            {/* Service Section */}
            <div className="service">
              <h2>Health service for you</h2>
              <div className="service-buttons">
                <div
                  className="service-box"
                  onClick={() => scrollToSection(infoRef)}
                >
                  <FontAwesomeIcon
                    className="clover"
                    icon={faClover}
                    size="2x"
                    color="#00b894"
                  />
                  <h3>HEALTH TRACKING</h3>
                  <p>Easily manage your health</p>
                </div>
                <div
                  className="service-box"
                  onClick={() => scrollToSection(serviceRef)}
                >
                  <FontAwesomeIcon
                    className="pills"
                    icon={faCapsules}
                    size="2x"
                    color="#00cec9"
                  />
                  <h3>Medication Reminders</h3>
                  <p>Taking your medicine just got easier</p>
                </div>
                <div
                  className="service-box"
                  onClick={() => scrollToSection(supportRef)}
                >
                  <FontAwesomeIcon
                    className="meal"
                    icon={faBowlFood}
                    size="2x"
                    color="#fab1a0"
                  />
                  <h3>Personalized Meal Plans</h3>
                  <p>Create meal plans tailored to your health status and goals</p>
                </div>
              </div>
            </div>
    
            {/* Sections to scroll to */}
            <div ref={infoRef} id="info" className="section">
              <h3>HEALTH TRACKING</h3>
              <p>
              Easily manage your health! Record key metrics such as heart rate,
              blood pressure, weight, and daily activity levels. View visual
              reports to track your body's changes over time.
            </p>
            <ul>
              <li>✅ Measure and store health data</li>
              <li>✅ Update charts by day, week, and month</li>
              <li>✅ Analyze trends and provide alerts for unusual signs</li>
            </ul>

            </div>
    
            <div ref={serviceRef} id="service" className="section">
              <h3>Fast and Convenient Medical Services</h3>
              <p>Book doctor appointments online with ease...</p>
            </div>
    
            <div ref={supportRef} id="support" className="section">
              <h3>Personalized Health Support Tools</h3>
              <p>Track your body metrics and get tailored health plans...</p>
            </div>
          </div>
        </div>
    )
}
