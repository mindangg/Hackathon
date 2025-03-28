import React, { useState, useEffect, useRef } from 'react';
import Webcam from 'react-webcam';
import Lottie from 'react-lottie-player';
import talkingAnimation from '../animations/avatar.json';

import { useAuthContext } from '../hooks/useAuthContext';

import '../styles/Chatbot.css';

export default function Chatbot() {
    const { user } = useAuthContext()

    const [messages, setMessages] = useState([
        { sender: 'Therapist', text: 'Hello! How are you feeling today?' },
    ]);
    const [input, setInput] = useState('');
    const [showWebcam, setShowWebcam] = useState(true);
    const [emotion, setEmotion] = useState('');
    const [isSpeaking, setIsSpeaking] = useState(false);
    const webcamRef = useRef(null);
    const messagesEndRef = useRef(null);
    const latestMessageRef = useRef(null);

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

    const speakText = (text) => {
        if (!text || text === latestMessageRef.current) return;
        latestMessageRef.current = text;

        setIsSpeaking(true);

        const speech = new SpeechSynthesisUtterance(text);
        speech.lang = 'en-US';

        speech.onend = () => setIsSpeaking(false);

        speechSynthesis.speak(speech);
    };

    const captureAndAnalyzeEmotion = async () => {
        if (!webcamRef.current) {
            console.error('Webcam reference is not available.');
            return;
        }
    
        // const imageSrc = webcamRef.current.getScreenshot();
        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) {
            console.error('Failed to capture image from webcam.');
            return;
        }
    
        try {
            const blob = await fetch(imageSrc).then(res => res.blob());
            const formData = new FormData();
            formData.append('file', blob, 'image.jpg');
    
            const response = await fetch('http://localhost:5000/analyze-emotion', {
                method: 'POST',
                body: formData,
            });
    
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} - ${response.statusText}`);
            }
    
            const data = await response.json();
            console.log('Full API Response:', data);
    
            const detectedEmotion = data?.dominant_emotion || 'unknown';
            console.log('Emotion detected:', detectedEmotion);
    
            if (detectedEmotion !== 'unknown') {
                setEmotion(detectedEmotion);
                setMessages((prevMessages) => [
                    ...prevMessages,
                    { sender: 'Therapist', text: `I see you're feeling ${detectedEmotion}. Let's talk about it.` }
                ]);
            } 
            else {
                console.warn('No dominant emotion detected.');
            }
        } 
        catch (error) {
            console.error('Error analyzing emotion:', error);
        }
    };    

    const handleSend = async () => {
        if (input.trim() === '') return;

        if (!showWebcam) setShowWebcam(true);

        setMessages(prevMessages => [
            ...prevMessages,
            { sender: 'You', text: input }
        ]);

        try {
            const response = await fetch('http://localhost:4000/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.user._id, message: input })
            });

            const json = await response.json();
            console.log(json)
            setMessages(prevMessages => [
                ...prevMessages,
                { sender: 'Therapist', text: json.response }
            ]);

            speakText(json.sentiment_response);
        }
        catch (error) {
            console.error('Error sending message:', error);
        }

        setInput('');
    };

    useEffect(() => {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage?.sender === 'Therapist') {
            speakText(lastMessage.text);
        }
    }, [messages]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className='chatbot-container'>

            <div className='chatbot-avatar'>
                <Lottie
                    loop
                    animationData={talkingAnimation}
                    play={isSpeaking}
                    style={{ width: 500, height: 500 }}
                />
            </div>

            {showWebcam && (
                <div className='webcam-popup'>
                    <Webcam ref={webcamRef} screenshotFormat='image/jpeg' width={300} height={180} />
                    <div className='webcam-btn'>
                        <button onClick={captureAndAnalyzeEmotion}>Analyze Emotion</button>
                    </div>
                    <div className='web-emo'>
                        <p>Detected Emotion: {emotion || 'Unknown'}</p>
                    </div>
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
