import React, { useState } from 'react'
import '../styles/Chatbot.css'

export default function Chatbot() {
    const [messages, setMessages] = useState([
        { sender: 'Therapist', text: 'Hello! How are you feeling today?' },
    ])
    const [input, setInput] = useState('')

    const handleSend = async () => {
        if (input.trim() === '') 
            return

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

            console.log(json)

            setMessages(prevMessages => [...prevMessages, { sender: 'Therapist', text: json.reply }])

        } 
        catch (error) {
            console.error('Error sending message:', error)
        }

        setInput('')
    }

    return (
        <div className='chatbot-container'>
            <div className='chatbot-messages'>
                {messages.map((msg, index) => (
                    <div key={index} className={`chatbot-message ${msg.sender === 'You' ? 'chatbot-request' : 'chatbot-response'}`}>
                        <h4>{msg.sender}</h4>
                        <p>{msg.text}</p>
                    </div>
                ))}
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
