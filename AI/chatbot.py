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
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb+srv://mindang:mindang@mernapp.nxyjt.mongodb.net/?retryWrites=true&w=majority&appName=MERNapp")  
db = client["ai_therapist"]
users_collection = db["user_emotions"]

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
    "amazing": "happy"
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


def store_emotion(user_id, message, emotion, confidence):
    users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {"last_emotion": emotion},
            "$push": {
                "emotions_history": {
                    "$each": [{"emotion": emotion, "confidence": confidence}],
                    "$slice": -20  # Keeps only the last 20 entries
                }
            }
        },
        upsert=True  # Ensures a new user record is created if one doesn't exist
    )

# def get_emotional_trends(user_id, limit=20):
#     user_data = users_collection.find_one({"user_id": user_id}, {"emotions_history": 1})
#     if not user_data or "emotions_history" not in user_data:
#         return {}

#     emotions_history = user_data["emotions_history"][-limit:]

#     if not emotions_history:
#         return {}

#     emotion_counts = {}
#     for entry in emotions_history:
#         emotion = entry["emotion"]
#         emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

#     total = len(emotions_history)
#     if total == 0:
#         return {}

#     emotion_trends = {k: v / total for k, v in emotion_counts.items()}
#     return emotion_trends

def get_emotional_trends(user_id, limit=20, scale_total=10):
    user_data = users_collection.find_one({"user_id": user_id}, {"emotions_history": 1})
    
    if not user_data or "emotions_history" not in user_data:
        return {}

    emotions_history = user_data["emotions_history"]

    # **Ensure at least 10 emotions exist before proceeding**
    if len(emotions_history) < 10:
        return {}

    # Get the last `limit` emotions
    emotions_history = emotions_history[-limit:]

    # Count occurrences of each emotion
    emotion_counts = {}
    for entry in emotions_history:
        emotion = entry["emotion"]
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    total = len(emotions_history)
    if total == 0:
        return {}

    # Scale counts to sum to `scale_total`
    scaled_trends = {k: round((v / total) * scale_total) for k, v in emotion_counts.items()}

    # Ensure the total sum remains `scale_total`
    adjustment = scale_total - sum(scaled_trends.values())

    # Adjust rounding errors (adds/subtracts from largest value)
    if adjustment != 0 and scaled_trends:
        max_emotion = max(scaled_trends, key=scaled_trends.get)
        scaled_trends[max_emotion] += adjustment

    return scaled_trends


def get_last_trend_sent(user_id):
    user_data = users_collection.find_one({"user_id": user_id}, {"last_trend_sent": 1})
    if not user_data or "last_trend_sent" not in user_data:
        return None

    last_sent = user_data["last_trend_sent"]
    if isinstance(last_sent, datetime):
        return last_sent if last_sent.tzinfo else last_sent.replace(tzinfo=timezone.utc)
    return None

def mark_trend_as_sent(user_id):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_trend_sent": datetime.now(timezone.utc)}},
        upsert=True
    )

TREND_COOLDOWN = timedelta(minutes=10)  # Allow quick response to sudden shifts

# def get_last_distinct_emotions(user_id):
#     """Retrieve the last two DISTINCT recorded emotions for the user."""
#     user_data = users_collection.find_one({"user_id": user_id}, {"emotions_history": 1})
#     if not user_data or "emotions_history" not in user_data:
#         return None, None

#     emotions_history = user_data["emotions_history"]

#     # Extract distinct emotions in reverse order
#     seen = set()
#     distinct_emotions = []

#     for entry in reversed(emotions_history):
#         emotion = entry["emotion"]
#         if emotion not in seen:
#             seen.add(emotion)
#             distinct_emotions.append(emotion)
#         if len(distinct_emotions) == 2:
#             break

#     if len(distinct_emotions) < 2:
#         return None, None  # Not enough distinct emotions

#     return distinct_emotions[1], distinct_emotions[0]  # Return (previous, latest)

def get_last_two_emotions(user_id):
    """Retrieve the last two recorded emotions for the user."""
    user_data = users_collection.find_one({"user_id": user_id}, {"emotions_history": 1})

    if not user_data or "emotions_history" not in user_data:
        return None, None

    emotions_history = user_data["emotions_history"]
    
    if len(emotions_history) < 2:
        return None, emotions_history[-1]["emotion"] if emotions_history else None
    
    return emotions_history[-2]["emotion"], emotions_history[-1]["emotion"]

# def get_last_emotion_change(user_id):
#     """Retrieve the last timestamp when the user's emotion significantly changed."""
#     user_data = users_collection.find_one({"user_id": user_id}, {"last_emotion_change": 1})

#     last_change = user_data.get("last_emotion_change")
#     if isinstance(last_change, datetime):
#         return last_change if last_change.tzinfo else last_change.replace(tzinfo=timezone.utc)
#     return None

# def mark_emotion_change(user_id):
#     """Mark when an emotional shift occurs."""
#     users_collection.update_one(
#         {"user_id": user_id},
#         {"$set": {"last_emotion_change": datetime.now(timezone.utc)}},
#         upsert=True
#     )

@app.post("/analyze")
async def chat_response(request: dict):
    try:
        user_id = request.get("user_id")
        message = request.get("message")

        if not user_id or not message:
            raise HTTPException(status_code=400, detail="Missing user_id or message")
        
        # Preprocess user input
        processed_message = preprocess_text(message)

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
        else:
            final_label = "neutral"
            final_confidence = 1.0  # Default full confidence in neutral

        # Choose the highest weighted label
        final_label = max(label_scores, key=label_scores.get)
        final_confidence = label_scores[final_label]

        # **Handle neutral case** (low-confidence emotions)
        if final_confidence < 0.3:  # Lowered threshold from 0.4 to 0.3
            final_label = "neutral"

        # Add slight variation at the end
        response_variations = {
            "joy": [
                "What’s been making your day so great?",
                "What’s the best thing that happened today?",
                "What’s bringing you so much joy?",
                "What’s been the highlight?",
                "That must feel incredible! Want to share more about it?",
                "What’s something that made you smile today?",
                "You deserve this happiness! How are you celebrating?"
            ],
            "sadness": [
                "Do you need advice or just a listening ear?",
                "You’re not alone in this. Want to unpack it together?",
                "How are you holding up?",
                "Would you like to share more? I’m here to listen.",
                "I hear you. Do you want to explore that feeling further?",
                "Take your time. I'm here when you're ready.",
                "What’s been the hardest part for you?",
                "What can I do to support you?",
                "If you could change one thing about this situation, what would it be?",
            ],
            "anger": [
                "I see this is frustrating for you. Want to talk about it?",
                "That must have been really upsetting. What happened?",
                "It makes sense why you’d feel this way. What’s on your mind?",
                "I hear you. Let’s talk through it together.",
                "If you could change one thing about this situation, what would it be?",
                "Do you want to vent, or should I offer some perspective?",
                "That seems important to you. Let’s talk about it."
            ],
            "fear": [
                "Do you want to talk more about it?",
                "You’re safe here. What’s making you feel this way?",
                "Would you like to share more?",
                "Fear can be tough to deal with. Take your time—I'm here.",
                "How can I support you?",
                "It’s okay to feel this way. What else is going on?",
                "How can I best support you right now?"
            ],
            "neutral": [
                "How does that make you feel?",
                "Tell me more.",
                "I’m here to listen.",
                "That sounds important. Let's discuss.",
                "I'm all ears. What's on your mind?",
                "That makes sense. What else is going on?"
            ]
        }

        # Store emotion in database
        store_emotion(user_id, message, final_label, final_confidence)

        # Detect emotional shift BEFORE trends

        previous_emotion, last_emotion = get_last_two_emotions(user_id)
        # last_emotion_change = get_last_emotion_change(user_id)

        emotional_shift_response = ""

        trend_response = ""
        # if previous_emotion and last_emotion and last_emotion_change:
        #     time_since_change = now - last_emotion_change
            
        emotional_responses = {
            ("sadness", "joy"): "I’m glad to see you feeling happier! What helped lift your mood?",
            ("joy", "sadness"): "You seemed happy earlier. Did something happen that's making you feel down now?",
            ("anger", "neutral"): "You seemed upset before, but now you’re calmer. Did something help you feel better?",
            ("neutral", "anger"): "You were feeling neutral earlier, but now you’re upset. Want to talk about what’s bothering you?",
            ("fear", "neutral"): "You seemed anxious before, but now you're feeling more at ease. Did something reassure you?",
            ("neutral", "fear"): "You seemed fine earlier, but now you look worried. Is there something on your mind?",
            ("sadness", "anger"): "You were feeling down earlier, and now you're frustrated. Do you want to share what’s causing this shift?",
            ("anger", "sadness"): "You seemed angry before, but now you look sad. Did something change how you feel?",
            ("joy", "neutral"): "You were happy before, and now you're neutral. Is everything still going okay?",
            ("neutral", "joy"): "You seem to be in a better mood now! What made your day brighter?",
            ("fear", "sadness"): "You were feeling anxious before, and now you seem sad. Want to talk about what’s going on?",
            ("sadness", "fear"): "You seemed sad before, and now you look worried. Is there something making you anxious?"
        }

        if previous_emotion != last_emotion:
            emotional_shift_response = emotional_responses.get((previous_emotion, last_emotion))

        # Get emotional trends
        emotion_trends = get_emotional_trends(user_id)
        last_trend_sent = get_last_trend_sent(user_id)

        # **Check if trend response should be sent**
        now = datetime.now(timezone.utc)

        if (
            (last_trend_sent is None or now - last_trend_sent > TREND_COOLDOWN) and  # Only send if enough time has passed
            (
                emotion_trends.get("sadness", 0) > 6 or  # More than 60% of 10 (i.e., 7+ occurrences)
                emotion_trends.get("joy", 0) > 6 or 
                len(emotion_trends) > 3  # More than 3 distinct emotions detected
            )
        ):
            if emotion_trends.get("sadness", 0) > 6:
                trend_response = "I've noticed you've been feeling down frequently. Do you want to talk about what's been troubling you?"
            elif emotion_trends.get("joy", 0) > 6:
                trend_response = "You’ve been feeling great lately! What’s been keeping you in high spirits?"
            elif emotion_trends.get("anger", 0) > 6:
                trend_response = "You’ve been feeling quite frustrated or angry recently. Would you like to share what’s been bothering you?"
            elif emotion_trends.get("fear", 0) > 6:
                trend_response = "It seems like you've been feeling anxious or worried a lot. Is there something on your mind that I can help you with?"
            elif emotion_trends.get("neutral", 0) > 6:
                trend_response = "You’ve been feeling pretty neutral for a while. How have things been going for you lately?"
            elif len(emotion_trends) > 3:
                trend_response = "Your emotions have been shifting a lot. Want to explore what's causing these changes?"
            
            # **Mark trend as sent**
            mark_trend_as_sent(user_id)

        # Get a nuanced response
        nuanced_response = get_nuanced_response(final_label, final_confidence) or "I'm here to listen."

        # Select response variation based on detected emotion
        variation = random.choice(response_variations.get(final_label, response_variations["neutral"]))

        # Construct final response

        if emotional_shift_response:
            final_response = emotional_shift_response
        elif trend_response:
            final_response = trend_response
        else:
            final_response = f"{nuanced_response.strip()} {variation}"

        # Return response
        response_data = {
            "emotion": final_label,
            "confidence": final_confidence,
            "response": final_response
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

def preprocess_image(image):
    # image = cv2.resize(image, (224, 224))  # Resize for model compatibility
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB (DeepFace uses RGB)
    image = image / 255.0  # Normalize pixels
    return image

@app.post("/analyze-emotion")
async def analyze_emotion(file: UploadFile = File(...)):
    try:
        # Read and decode the image
        image_data = await file.read()
        image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Preprocess the image
        image = preprocess_image(image)

        # Perform emotion analysis using DeepFace
        results = DeepFace.analyze(
            image, 
            actions=['emotion'], 
            model_name="EfficientNet", 
            enforce_detection=True  # Enforce face detection for better accuracy
        )

        if not results:
            return {"dominant_emotion": "unknown", "emotion_scores": {}}

        # Extract emotions
        analysis = results[0]
        emotion_scores = {k: float(v) for k, v in analysis.get("emotion", {}).items()}
        dominant_emotion = analysis.get("dominant_emotion", "unknown")

        return {
            "dominant_emotion": dominant_emotion,
            "emotion_scores": emotion_scores
        }

    except HTTPException as http_err:
        raise http_err  # Preserve FastAPI HTTP exceptions
    except Exception as e:
        print(f"Error: {str(e)}")  # Log the error for debugging
        raise HTTPException(status_code=500, detail="Internal Server Error. Please try again.")