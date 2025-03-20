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

nlp.add_pipe("negex", config={"ent_types": ["ADJ", "VERB"]})

response_dict = {
    "joy": {
        "mild": [
            "That’s great to hear! What’s something small that made you smile today?",
            "A little happiness goes a long way! What’s making you feel good?",
            "I love that energy! Anything fun happening today?",
            "Even the smallest joys are worth celebrating. Tell me about it!",
            "It’s always nice to hear good news! What’s been making you feel good?",
            "Happiness is contagious! What’s something positive that happened recently?",
            "Small wins matter too! What’s one thing that made you feel good today?"
        ],
        "moderate": [
            "That sounds wonderful! What’s been the highlight of your day?",
            "Your happiness is contagious! What’s making today special?",
            "Love to hear that! Tell me more about what’s making you happy.",
            "Happiness is a great feeling! Is there something exciting happening?",
            "I can feel the positivity from here! What’s been making your day so great?",
            "That’s amazing! Have you shared your happiness with someone today?",
            "Good vibes all around! What’s something exciting you’ve been looking forward to?"
        ],
        "intense": [
            "Wow, you sound over the moon! What’s bringing you so much joy?",
            "That’s amazing! What’s the best part of your day so far?",
            "I can feel your excitement! What’s making you this happy?",
            "You’re glowing with happiness! What’s the most exciting thing that happened?",
            "This is amazing! What’s making you feel so overjoyed?",
            "You must be on top of the world right now! Tell me everything!",
            "Your happiness is radiating! What’s been the best part of your day?",
            "Wow, this sounds like a moment to remember! How are you celebrating?",
            "That level of excitement is incredible! What’s made this day so special?",
            "I love hearing this kind of joy! What’s something you’ll always remember about today?",
            "Your excitement is contagious! What’s one thing that made this so amazing?"
        ]
    },
    "sadness": {
        "mild": [
            "I hear you. It’s okay to feel a little down sometimes.",
            "A tough moment doesn’t define your whole day. Want to talk about it?",
            "I’m here for you. Do you want to share what’s on your mind?",
            "It’s completely okay to feel this way. What’s bothering you?",
            "I understand. Even small struggles can feel big sometimes. What’s been going on?",
            "I’m here to listen if you want to talk.",
            "You’re not alone in this. What’s been weighing on you?"
        ],
        "moderate": [
            "I know things feel heavy right now. You’re not alone in this.",
            "Your feelings are valid. Want to talk about what’s been on your mind?",
            "Sometimes just talking helps. I’m here whenever you’re ready.",
            "It’s okay to have these feelings. What’s making you feel this way?",
            "You don’t have to go through this alone. I’m here for you.",
            "I can tell this is tough. Do you want to share more about what’s been happening?",
            "You’re doing the best you can, and that’s enough. What’s been hardest for you?"
        ],
        "intense": [
            "I’m really sorry you’re feeling this way. I’m here for you.",
            "You’re not alone. Even when it feels like it, there are people who care about you.",
            "I wish I could give you a big hug right now. You deserve kindness and support.",
            "If you’re struggling, know that you don’t have to go through this alone. I’m here.",
            "This must be really hard for you. I want to support you however I can.",
            "You’re stronger than you think, even when it doesn’t feel that way.",
            "Please be kind to yourself. You deserve care and understanding.",
            "I’m really sorry you’re going through this. You’re not alone.",
            "You deserve kindness and support. I’m here for you.",
            "If this feels overwhelming, please reach out to someone you trust.",
            "I wish I could take away your pain. Just know that you are valued and cared for.",
            "You are stronger than you feel right now. I’m here to support you.",
            "I can’t imagine how hard this must be, but I’m here to listen.",
            "Even in your darkest moments, you are not alone. I care about you."
        ]
    },
    "anger": {
        "mild": [
            "I see you’re a little frustrated. Want to talk about it?",
            "That sounds annoying! What happened?",
            "It’s okay to feel this way. What’s been on your mind?",
            "Frustration happens to everyone. Do you want to vent?",
            "That must have been frustrating. How can I help?",
            "I get why that would bother you. Want to talk it out?",
            "Sometimes little things build up. What’s been going on?"
        ],
        "moderate": [
            "I hear you, that sounds really upsetting. What’s going on?",
            "It sounds like this really got to you. Want to talk through it?",
            "That must have been really frustrating. I’m here to listen.",
            "I understand why you’re upset. Let’s figure this out together.",
            "Anger is a natural reaction. What’s making you feel this way?",
            "It’s okay to let it out. What’s been bothering you the most?",
            "You deserve to be heard. Tell me what happened."
        ],
        "intense": [
            "I can tell you’re really upset. Take a deep breath – I’m here.",
            "That sounds really difficult. I want to support you however I can.",
            "Anger can be overwhelming. Want to talk about it?",
            "Let’s work through this together. You don’t have to deal with it alone.",
            "I hear you loud and clear. What’s making you feel this way?",
            "I understand your frustration. How can I help you feel better?",
            "It’s okay to be upset. I’m here to listen without judgment."
        ]
    },
    "fear": {
        "mild": [
            "That sounds a little unsettling. Want to talk about it?",
            "I understand. Fear can be tough to deal with.",
            "It’s okay to feel uneasy sometimes. What’s making you feel this way?",
            "You’re safe here. Do you want to share what’s on your mind?",
            "I hear you. It’s normal to feel nervous sometimes.",
            "That must have made you uncomfortable. Do you want to talk about it?",
            "Fear can be overwhelming, but you’re not alone."
        ],
        "moderate": [
            "That sounds really scary. I’m here to listen.",
            "Fear can feel overwhelming, but you’re not alone.",
            "I hear you. Facing fears is hard, but you’re strong.",
            "You don’t have to go through this alone. I’m here.",
            "I know that feeling can be difficult to manage. What’s making you feel this way?",
            "It’s okay to be afraid. I’ll be here for you while you work through it.",
            "I understand why you’re scared. Let’s talk about it together."
        ],
        "intense": [
            "That sounds terrifying. I want to help you feel safe.",
            "You’re not alone. I believe in your strength to get through this.",
            "It’s okay to be scared. I’m here with you every step of the way.",
            "Take a deep breath. I’m right here with you.",
            "That must have been really frightening. Do you want to share more about it?",
            "You don’t have to face this alone. I’m here for you.",
            "It’s okay to let yourself feel scared. You’re not in this alone."
        ]
    },
    "neutral": {
        "default": [
            "I see. Tell me more if you’d like.",
            "Got it. How do you feel about that?",
            "I’m listening. What’s on your mind?",
            "Understood. Is there anything else you’d like to share?"
        ]
    }
}


# Load spaCy for sentence parsing
nlp = spacy.load("en_core_web_sm")

# Improved negation mapping (handling more cases)
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
    "not great": "bad",
    "not good": "bad",  # Added this
    "don't feel good": "feel bad",  # Fix for "I don't feel good"
    "do not feel good": "feel bad",
    "don't feel bad": "feel neutral",
    "do not feel bad": "feel neutral",
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
        elif token.text in ["not", "n't"] and i + 1 < len(doc) and doc[i + 1].pos_ in ["ADJ", "VERB"]:
            # Handle negations before adjectives or verbs
            negated_word = negation_mapping.get(doc[i + 1].text, f"not_{doc[i + 1].text}")
            new_text.append(negated_word)
            skip_next = True
        else:
            new_text.append(token.text)

    processed_text = " ".join(new_text)
    
    # Debugging Output
    print(f"Original: {text}")
    print(f"Processed: {processed_text}")

    return processed_text

# Function to get a response based on emotion and confidence level
def get_nuanced_response(emotion, confidence):
    intensity = (
        "intense" if confidence >= 0.8 else
        "moderate" if confidence >= 0.55 else
        "mild" if confidence >= 0.3 else
        "default"
    )

    # Get responses safely
    emotion_responses = response_dict.get(emotion, response_dict["neutral"])  # Default to "neutral"
    intensity_responses = emotion_responses.get(intensity, response_dict["neutral"]["default"])  # Default to neutral's default responses
    
    return random.choice(intensity_responses)


@app.post("/analyze")
async def chat_response(request: dict):
    try:
        processed_message = preprocess_text(request["message"])

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
        if final_confidence < 0.3:  # Lowered threshold from 0.4 to 0.3
            final_label = "neutral"

        # Get a response
        response = get_nuanced_response(final_label, final_confidence)

        # Add slight variation at the end
        variation = random.choice([
            "How does that make you feel?",  
            "Want to talk more about it?",  
            "Tell me more.",  
            "I'm here to listen.",  
            "That sounds important. Let's discuss.",  
            "I'm all ears. What's on your mind?",  
            "That must be a lot to process.",  
            "Would you like to share more?",  
            "You’re not alone in this. Want to unpack it together?",  
            "That makes sense. What else is going on?",  
            "I hear you. Do you want to explore that feeling further?",  
            "Take your time. I'm here when you're ready.",  
            "That sounds tough. Do you need advice or just a listening ear?",  
            "What’s been the hardest part for you?",  
            "If you could change one thing about this situation, what would it be?",  
            "It’s okay to feel this way. What can I do to support you?",  
            "Do you want to vent, or should I offer some perspective?",  
            "That seems important to you. Let’s talk about it.",  
            "How can I best support you right now?"  
        ])

        return {
            "emotion": final_label,
            "confidence": final_confidence,
            "response": f"{response} {variation}"
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
        analysis = DeepFace.analyze(image, actions=['emotion'], enforce_detection=False)

        if not analysis:  # No face detected
            return {"dominant_emotion": "unknown", "emotion_scores": {}}

        analysis = analysis[0]  # Extract first face detected

        emotion_scores = {k: float(v) for k, v in analysis.get("emotion", {}).items()}
        dominant_emotion = analysis.get("dominant_emotion", "unknown")

        return {
            "dominant_emotion": dominant_emotion,
            "emotion_scores": emotion_scores
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))