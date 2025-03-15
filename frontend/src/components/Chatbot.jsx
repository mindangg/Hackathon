import React, { useState, useEffect, useRef } from 'react'
import '../styles/Chatbot.css'

export default function Chatbot() {
    const [messages, setMessages] = useState([
        { sender: 'Therapist', text: 'Hello! How are you feeling today?' },
    ])
    const [input, setInput] = useState('')
    const messagesEndRef = useRef(null)

    const handleSend = async () => {
        if (input.trim() === '') return

        setMessages([...messages, { sender: 'You', text: input }])

        try {
            const response = await fetch('http://localhost:4000/api/chatbot', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ message: input })
            })

            const json = await response.json()
            setMessages(prevMessages => [...prevMessages, { sender: 'Therapist', text: json }])
        } 
        catch (error) {
            console.error('Error sending message:', error)
        }

        setInput('')
    }

    // Tự động cuộn xuống tin nhắn mới nhất
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    return (
        <div className='chatbot-container'>
            <div className='chatbot-messages'>
                {messages.map((msg, index) => (
                    <div key={index} className={`chatbot-message ${msg.sender === 'You' ? 'chatbot-request' : 'chatbot-response'}`}>
                        <h4>{msg.sender}</h4>
                        <p>{msg.text}</p>
                    </div>
                ))}
                <div ref={messagesEndRef} /> {/* Phần tử rỗng để cuộn xuống */}
            </div>

            <div className='chatbot-input'>
                <input 
                    type='text' 
                    placeholder='Type a message...' 
                    value={input} 
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                />
                <button onClick={handleSend}>Send</button>
            </div>
        </div>
    )
}
