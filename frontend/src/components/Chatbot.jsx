import React, { useState, useEffect, useRef } from 'react';
import Webcam from 'react-webcam';
import '../styles/Chatbot.css';

export default function Chatbot() {
    const [messages, setMessages] = useState([
        { sender: 'Therapist', text: 'Hello! How are you feeling today?' },
    ]);
    const [input, setInput] = useState('');
    const [showWebcam, setShowWebcam] = useState(false);
    const [emotion, setEmotion] = useState('');
    const webcamRef = useRef(null);
    const messagesEndRef = useRef(null);

    // Speech-to-Text
    const startListening = () => {
        setInput('');
        const recognition = new window.webkitSpeechRecognition() || new window.SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.start();

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            setInput(transcript);
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
        };
    };

    // Text-to-Speech
    const speakText = (text) => {
        const speech = new SpeechSynthesisUtterance(text);
        speech.lang = 'en-US';
        speechSynthesis.speak(speech);
    };

    // Capture and Analyze Facial Emotion
    const captureAndAnalyzeEmotion = async () => {
        if (!webcamRef.current) return;
    
        const imageSrc = webcamRef.current.getScreenshot();
        const blob = await fetch(imageSrc).then(res => res.blob());
    
        const formData = new FormData();
        formData.append("file", blob, "image.jpg");
    
        try {
            const response = await fetch("http://localhost:5000/analyze-emotion", {
                method: "POST",
                body: formData,
            });
    
            const data = await response.json();
            console.log("Emotion detected:", data.emotion);
    
            if (data.emotion) {
                setEmotion(prevEmotion => data.emotion);  // Ensure state updates properly
    
                setMessages(prevMessages => [
                    ...prevMessages, 
                    { sender: 'Therapist', text: `I see you're feeling ${data.emotion}. Let's talk about it.` }
                ]);
    
                speakText(`I see you're feeling ${data.emotion}. Let's talk about it.`);
            }
        } catch (error) {
            console.error("Error analyzing emotion:", error);
        }
    };

    const handleSend = async () => {
        if (input.trim() === '') return;
        
        if (!showWebcam) setShowWebcam(true);

        setMessages([...messages, { sender: 'You', text: input }]);

        try {
            const response = await fetch('http://localhost:4000/api/chatbot', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ message: input })
            });

            const json = await response.json();
            setMessages(prevMessages => {
                const newMessages = [...prevMessages, { sender: 'Therapist', text: json.response }];
                speakText(json.response);
                return newMessages;
            });
        } 
        catch (error) {
            console.error('Error sending message:', error);
        }

        setInput('');
    };

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className='chatbot-container'>
            {showWebcam && (
                <div className='webcam-popup'>
                    <Webcam ref={webcamRef} screenshotFormat="image/jpeg" width={300} height={180} />
                    <button onClick={captureAndAnalyzeEmotion}>Analyze Emotion</button>
                    <p>Detected Emotion: {emotion || "Unknown"}</p>
                </div>
            )}
            <div className='chatbot-messages'>
                {messages.map((msg, index) => (
                    <div key={index} className={`chatbot-message ${msg.sender === 'You' ? 'chatbot-request' : 'chatbot-response'}`}>
                        <h4>{msg.sender}</h4>
                        <p>{msg.text}</p>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            <div className='chatbot-input'>
                <input 
                    type='text' 
                    placeholder='Type a message...' 
                    value={input} 
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                />
                <button onClick={startListening}>🎤</button>
                <button onClick={handleSend}>Send</button>
            </div>
        </div>
    );
}
