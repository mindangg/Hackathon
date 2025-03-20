from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import torch
import random
import whisper
from gtts import gTTS
import os
import tempfile
import cv2
import numpy as np
from deepface import DeepFace
from transformers import pipeline
import spacy
from negspacy.negation import Negex
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models
whisper_model = whisper.load_model("base")

emotion_pipeline1 = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")
emotion_pipeline2 = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

class MessageRequest(BaseModel):
    message: str

# Load Spacy NLP model for negation detection
nlp = spacy.load("en_core_web_sm")

nlp.add_pipe("negex")

response_dict = {
    "joy": [
        "That's amazing! Keep spreading positivity!", 
        "You sound happy! What's making your day great?",
        "Happiness is contagious! Tell me what’s bringing you joy today.",
        "That’s wonderful! Savor the good moments.",
        "I love hearing that! What’s something exciting happening for you?",
        "It's great to hear you’re feeling happy! Anything in particular that made your day?",
        "Keep smiling! The world needs more joy.",
        "Sounds like a great day! What’s been the highlight so far?",
        "Good vibes all around! Want to share what’s making you so cheerful?",
        "Happiness suits you! What’s been going well lately?",
        "That’s such a positive thing to hear! What’s bringing you so much joy?",
        "You deserve happiness! What’s something you’re looking forward to?",
        "Your happiness shines through! I’d love to hear what’s making you smile.",
        "Life’s little joys are worth celebrating! What’s making you feel this way?",
        "It’s great to see you happy! What’s one thing that brought you joy today?"
    ],
    "sadness": [
        "I'm here for you. Want to talk about it?", 
        "It's okay to feel sad sometimes. You're not alone.",
        "I hear you. If you need someone to listen, I'm here.",
        "It’s completely okay to feel down. I’m here to support you.",
        "Would you like to talk about what’s on your mind?",
        "You are not alone in this. I’m here whenever you want to share.",
        "If it helps, I can listen. No pressure, just support.",
        "Sometimes, just talking about it can make a difference. I’m here.",
        "I wish I could give you a big hug right now. You’re not alone.",
        "You’re stronger than you think. I believe in you.",
        "I know it’s tough right now, but brighter days are ahead.",
        "Your feelings are valid. I’m here to support you however I can.",
        "You’re doing your best, and that’s enough. I’m here for you.",
        "I understand how heavy sadness can feel. You don’t have to carry it alone.",
        "Lean on me whenever you need. You don’t have to go through this alone."
    ],
    "anger": [
        "I see you're upset. Do you want to share what's bothering you?", 
        "It's okay to feel angry. Let's try to find a solution together.",
        "Anger is a valid feeling. What happened?",
        "I hear your frustration. Want to vent?",
        "It’s okay to feel this way. I’m here to listen without judgment.",
        "Do you want to talk about it or find ways to cool down? Either way, I’m here.",
        "What’s on your mind? Sometimes putting feelings into words helps.",
        "Anger can be tough to deal with, but I’m here to help you through it.",
        "If you need to express how you feel, I’m here for you.",
        "I understand that things can get frustrating. You’re not alone in this.",
        "I can see that something really upset you. Do you want to work through it together?",
        "Anger is a natural response. Let’s take a deep breath and talk it out.",
        "Would you like to focus on solutions or just vent for now? I’m here for either.",
        "It’s okay to feel this way. How can I help make things a little better?",
        "You don’t have to deal with this alone. I’m here to listen and support you."
    ],
    "surprise": [
        "That sounds unexpected! What happened?", 
        "Wow! That must have been a shock!",
        "That sounds like quite the twist! Want to tell me more?",
        "Unexpected moments can be exciting! What’s going on?",
        "Whoa! That must have caught you off guard. How do you feel about it?",
        "Surprises can be thrilling or overwhelming. Which one is this for you?",
        "I wasn’t expecting that either! Tell me more!",
        "Did this surprise make your day better or more complicated?",
        "I love surprises! Unless they’re the bad kind. Which one was this?",
        "Life has a way of throwing curveballs! How are you feeling about it?",
        "Surprises keep life interesting! Was this a good one or a challenging one?",
        "Wow! That must have been a moment to remember. What happened?",
        "Not every day brings surprises! How did this one make you feel?",
        "A twist in the story! Was it a happy or shocking surprise?",
        "Tell me more! I’d love to hear how this surprise unfolded."
    ],
    "fear": [
        "That sounds scary. Want to talk about it?", 
        "It's okay to be afraid. You're safe here.",
        "Fear is a natural response. What’s making you feel this way?",
        "You don’t have to face this alone. I’m here.",
        "Sometimes talking about our fears can make them feel smaller. Want to share?",
        "I hear you. Fear can be overwhelming, but you’re not alone.",
        "Take a deep breath. I’m right here with you.",
        "It’s okay to be scared. Do you want to talk through it?",
        "I want to help you feel safe. What’s on your mind?",
        "You’re stronger than your fears. I believe in you.",
        "Fear can feel paralyzing, but you don’t have to face it alone.",
        "Let’s take this one step at a time. I’m right here with you.",
        "You’re in a safe space. Tell me what’s on your mind.",
        "I understand why this feels scary. Let’s talk through it together.",
        "Courage doesn’t mean the absence of fear; it means facing it. You’ve got this."
    ],
    "disgust": [
        "That doesn't sound pleasant. What happened?", 
        "I get that. Some things can be really off-putting.",
        "That sounds really unpleasant. Do you want to share more about it?",
        "I understand why you’d feel that way. What’s going on?",
        "It’s okay to feel disgusted. Some things just don’t sit right.",
        "Ugh, that doesn’t sound great at all. Tell me about it.",
        "I can imagine how that would be upsetting. What happened?",
        "Some things just don’t feel right. Want to talk about it?",
        "Your feelings are valid. What made you feel this way?",
        "I totally get that. Some things are just hard to deal with.",
        "That must have been really unpleasant! Do you want to vent about it?",
        "Yikes! That doesn’t sound fun at all. What happened?"
    ],
    "neutral": [
        "I see. Tell me more if you’d like.",
        "Got it. How do you feel about that?",
        "I’m listening. What’s on your mind?",
        "Understood. Is there anything else you’d like to share?",
        "Alright. Let me know if there’s anything I can do.",
        "That makes sense. What else is going on?",
        "Okay, I’m here to listen whenever you need.",
        "I hear you. Do you want to talk more about it?",
        "Sounds like a balanced perspective. Anything else on your mind?",
        "I appreciate you sharing that. Would you like to expand on it?",
        "Thanks for telling me. What else is new?",
        "Neutral days can be good too. Anything interesting happening?",
    ]
}

# Load spaCy for sentence parsing
nlp = spacy.load("en_core_web_sm")

# Improved negation mapping (including direct replacements for "not bad" cases)
negation_mapping = {
    "bad": "good",
    "terrible": "okay",
    "sad": "neutral",
    "unhappy": "happy",
    "angry": "calm",
    "scared": "brave",
    "nervous": "confident",
    "upset": "calm",
    "stressed": "relaxed",
    "worried": "assured",
    "anxious": "peaceful",
    "afraid": "courageous",
    "disappointed": "satisfied",
    "frustrated": "patient",
    "lonely": "connected",
    "depressed": "hopeful",
    "pessimistic": "optimistic",
    "hopeless": "hopeful",
    "weak": "strong",
    "hesitant": "decisive",
    "indifferent": "engaged",
    "annoyed": "tolerant",
    "miserable": "content",
    "bored": "interested",
    "tired": "energetic",
    "sick": "healthy",
    "broken": "whole",
    "confused": "clear-headed",
    "lost": "focused",
    "discouraged": "motivated",
    "shy": "outgoing",
    "hostile": "friendly",
    "cruel": "kind",
    "insecure": "confident",
    "doubtful": "certain",
    "resistant": "receptive",
    "unstable": "steady",
    "restless": "peaceful",
    "hesitant": "assertive",
    "discouraged": "determined",
}

# Special cases where "not X" should be mapped directly
negation_phrases = {
    "not bad": "good",
    "not terrible": "okay",
    "not sad": "neutral",
    "not unhappy": "happy",
    "not angry": "calm",
    "not scared": "brave",
    "not nervous": "confident",
    "not upset": "calm",
    "not stressed": "relaxed",
    "not worried": "assured",
    "not anxious": "peaceful",
    "not afraid": "courageous",
    "not disappointed": "satisfied",
    "not frustrated": "patient",
    "not lonely": "connected",
    "not depressed": "hopeful",
    "not pessimistic": "optimistic",
    "not hopeless": "hopeful",
    "not weak": "strong",
    "not hesitant": "decisive",
    "not indifferent": "engaged",
    "not annoyed": "tolerant",
    "not miserable": "content",
    "not bored": "interested",
    "not tired": "energetic",
    "not sick": "healthy",
    "not broken": "whole",
    "not confused": "clear-headed",
    "not lost": "focused",
    "not discouraged": "motivated",
    "not shy": "outgoing",
    "not hostile": "friendly",
    "not cruel": "kind",
    "not insecure": "confident",
    "not doubtful": "certain",
    "not resistant": "receptive",
    "not unstable": "steady",
    "not restless": "peaceful",
    "not hesitant": "assertive",
    "not discouraged": "determined",
    "not great": "bad",  # Added this to handle 'not great' cases
}

def preprocess_text(text: str) -> str:
    """
    Processes the text to handle negations and improve sentiment detection.
    Uses NLP to ensure proper context handling.
    """
    text = text.lower().strip()

    # Check for direct negation phrases
    for phrase, replacement in negation_phrases.items():
        if phrase in text:
            text = text.replace(phrase, replacement)

    doc = nlp(text)  # Process with spaCy for sentence structure

    new_text = []
    skip_next = False

    for i, token in enumerate(doc):
        if skip_next:
            skip_next = False
            continue

        # Detect negation before a mapped word
        if token.dep_ == "neg" and token.head.text in negation_mapping:
            new_text.append(negation_mapping[token.head.text])  # Replace with mapped word
            skip_next = True  # Skip the next word to avoid redundancy
        elif token.text not in ["not", "n't"]:  # Remove "not" after replacing
            new_text.append(token.text)
    
    print(f"Original: {text}")
    print(f"Processed: {' '.join(new_text)}")

    return " ".join(new_text)

@app.post("/analyze")
async def chat_response(request: MessageRequest):
    try:
        processed_message = preprocess_text(request.message)

        # Get predictions in parallel
        results = [emotion_pipeline1(processed_message)[0], emotion_pipeline2(processed_message)[0]]

        # Confidence-weighted scoring system
        label_scores = {}
        total_confidence = 0

        for result in results:
            label = result['label'].lower()
            confidence = result['score']
            label_scores[label] = label_scores.get(label, 0) + confidence
            total_confidence += confidence

        # Normalize scores
        if total_confidence > 0:
            for label in label_scores:
                label_scores[label] /= total_confidence

        # Choose the highest weighted label
        final_label = max(label_scores, key=label_scores.get)
        final_confidence = label_scores[final_label]

        # **Handle neutral case** (low-confidence emotions)
        if final_confidence < 0.4:  # Threshold for neutrality
            final_label = "neutral"

        # Get a response
        response = random.choice(response_dict.get(final_label, ["I'm here for you."]))

        return {
            "emotion": final_label,
            "confidence": final_confidence,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/analyze")
# async def chat_response(request: MessageRequest):
#     try:
#         emotion_result = emotion_pipeline(request.message)[0]

#         label = emotion_result['label'].lower()
#         response = random.choice(response_dict.get(label, ["I'm here for you."]))

#         return {
#             "emotion": label,
#             "confidence": emotion_result['score'],
#             "response": response
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        text = whisper_model.transcribe(temp_path)["text"]
        os.unlink(temp_path)
        return {"transcribed_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text-to-speech")
async def text_to_speech(request: MessageRequest):
    try:
        tts = gTTS(request.message, lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            audio_path = temp_file.name
        tts.save(audio_path)
        return FileResponse(audio_path, media_type="audio/mpeg", filename="response.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-emotion")
async def analyze_emotion(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_data = await file.read()
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Perform emotion analysis
        analysis = DeepFace.analyze(image, actions=['emotion'], enforce_detection=False)[0]

        emotion_scores = {k: float(v) for k, v in analysis.get("emotion", {}).items()}
        dominant_emotion = analysis.get("dominant_emotion", "unknown")

        return {
            "dominant_emotion": dominant_emotion,
            "emotion_scores": emotion_scores
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))