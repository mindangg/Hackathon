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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Try this for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models
whisper_model = whisper.load_model("base")
sentiment_pipeline = pipeline("sentiment-analysis")

class MessageRequest(BaseModel):
    message: str

response_dict = {
    "POSITIVE_HIGH": [
        "That's amazing, try to keep it up!", "You’re doing great, keep pushing forward!", "I love that energy! Stay positive!", 
        "Happiness looks good on you!", "Keep up the good vibes!", "Wow, that's fantastic news!", "Glad to hear that! Keep going strong!", 
        "Your positivity is contagious!", "Awesome! Keep shining!", "That's the spirit! Keep it up!", 
        "You're truly inspiring!", "Stay strong and keep smiling!", "That’s wonderful to hear!", "You’re on the right path!", 
        "Every day is a new chance to shine!", "You are full of positive energy!", "Keep that fire burning!", "You deserve happiness!", 
        "Your attitude is admirable!", "Happiness is your natural state!", "Positivity looks great on you!", "You’re an inspiration!", 
        "Your enthusiasm is infectious!", "Keep being awesome!", "You make the world brighter!", "Success follows positivity!", 
        "Your happiness is your superpower!", "Every day is a blessing!", "Your mindset is incredible!", "Nothing can stop you!", 
        "Great things are coming your way!", "Your joy is limitless!", "You're living your best life!", "Shine on!", 
        "Happiness is a choice, and you chose well!", "Radiate good vibes!", "You deserve all the good in life!", 
        "Enjoy every moment!", "Keep aiming high!", "You bring joy to others!", "Your light shines bright!", 
        "You have a heart full of joy!", "Happiness is your default mode!", "Your optimism is refreshing!", "You were born to thrive!", 
        "The universe is cheering for you!", "You're glowing with positivity!", "Keep being you!", "You're unstoppable!", "Go get it, champion!",
        "Your positive outlook will take you far!", "Every day is another opportunity to shine!", "Your energy is magnetic!", 
        "Stay in this beautiful mindset!", "Good things keep happening to you!", "The world needs more people like you!", 
        "Your happiness fuels those around you!", "You are an endless source of joy!", "You are radiating success!", 
        "Life loves you back for all your positivity!", "Keep setting the world on fire with your light!", 
        "Everything you touch turns into something amazing!", "Your spirit is a beacon of inspiration!", "Happiness is your superpower!", 
        "Your light is undeniable!", "Keep walking this wonderful path of joy!", "Greatness suits you!", "Your energy transforms everything around you!", 
        "Every step you take is towards something amazing!", "You make the world a better place just by being you!", "You are proof that happiness wins!", 
        "You are a bright spark in this world!", "Everything about you radiates positivity!", "Your kindness and joy know no bounds!", 
        "Keep leading with love and light!", "The universe responds to your amazing energy!", "Your days will only get brighter!"
    ],

    "POSITIVE_LOW": [
        "That's great to hear!", "Nice! Keep enjoying your day!", "Good vibes only!", "That sounds really nice!", "Happy to hear that!", 
        "Glad things are going well for you!", "Positive energy suits you!", "Keep embracing the good moments!", 
        "Wishing you more amazing days ahead!", "Stay cheerful and keep spreading happiness!", "Smiling looks good on you!", 
        "Keep the momentum going!", "A great attitude makes a great day!", "Keep making wonderful memories!", "Enjoy the little things!", 
        "Keep the good energy flowing!", "Positivity attracts success!", "The best is yet to come!", "Keep up the good work!", 
        "Today is your day!", "Celebrate the small wins!", "You're making progress!", "Everything is falling into place!", 
        "Your energy is uplifting!", "You're on a roll!", "Hope your day stays awesome!", "You're making a difference!", 
        "Be proud of yourself!", "You're moving forward!", "Small joys make big impacts!", "A positive day leads to a positive life!", 
        "Great things are happening!", "You're stronger than you think!", "Life is good!", "Enjoy every second!", 
        "Your happiness is contagious!", "You’re spreading joy!", "Life is smiling at you!", "Your success is inspiring!", 
        "Every day is a fresh start!", "Keep spreading kindness!", "You're full of potential!", "You deserve happiness!", 
        "You're heading in the right direction!", "Success is just around the corner!", "Your positivity is powerful!", 
        "You make the world better!", "Your vibe attracts good things!", "You're a source of joy!", "The world needs your light!",
        "Small steps still lead to big achievements!", "Every effort you make counts!", "Your journey is unfolding beautifully!", 
        "Every day you are growing into the best version of yourself!", "Little joys add up to a beautiful life!", 
        "Keep being the amazing person you are!", "You make even an ordinary day feel special!", "Great energy attracts great experiences!", 
        "Good things keep happening for a reason!", "Life is rewarding your efforts!"
    ],

    "NEGATIVE_HIGH": [
        "I can feel that you're going through something really difficult. Please know that you are not alone.",
        "Sometimes, the weight of the world feels unbearable. Take a deep breath, and know that you are stronger than you think.",
        "It’s okay to feel overwhelmed. Try to give yourself the same compassion you would give to a friend.",
        "The storm may feel endless, but even the longest night will eventually meet the dawn.",
        "You matter, and what you’re feeling is real. Don’t be afraid to reach out for support.",
        "Even the hardest days will pass. Until then, be kind to yourself.",
        "Pain is real, but so is hope. Hold onto it, even if it feels small.",
        "There is strength in seeking help. You don’t have to go through this alone.",
        "Healing isn’t linear, and it’s okay to have setbacks. Keep going at your own pace.",
        "You are so much more than this difficult moment. Brighter days are ahead.",
        "No feeling is permanent. This pain won’t last forever.",
        "Your emotions are valid, and you have the right to feel and express them.",
        "Take a moment to pause, breathe, and remind yourself that you are enough.",
        "You are stronger than you believe, even when everything feels heavy.",
        "You deserve kindness, especially from yourself.",
        "Some days are harder than others, but each one brings you closer to healing.",
        "Try to focus on small things that bring comfort. Even the smallest light can guide you forward.",
        "You are loved, you are valued, and you are worthy of happiness.",
        "The road ahead might seem long, but you are not walking it alone.",
        "Take care of yourself the way you would take care of someone you love.",
        "You are not broken, and you are not beyond healing.",
        "Your struggles do not define you. You are so much more.",
        "Every difficult moment you survive makes you stronger.",
        "There are people who care about you, even when it doesn’t feel that way.",
        "You deserve rest, love, and healing.",
        "Even the smallest step forward is still progress.",
        "Your presence in this world matters. Never doubt that.",
        "It’s okay to not have all the answers right now.",
        "You are resilient. You have faced challenges before and overcome them.",
        "Tough times don’t last, but your strength does.",
        "Let yourself feel, but also remind yourself that better days are ahead.",
        "If today is hard, just focus on getting through this moment.",
        "Even when you feel alone, there is always hope.",
        "Your story isn’t over yet. There are still beautiful chapters ahead.",
        "Be patient with yourself. Healing takes time.",
        "You are doing the best you can, and that is enough.",
        "This moment is painful, but it does not define your entire life.",
        "It’s okay to ask for help. You don’t have to carry everything alone.",
        "Sometimes, the best thing you can do is take a deep breath and let yourself rest.",
        "You deserve happiness, even if it feels distant right now.",
        "There is hope, even in the darkest moments.",
        "Life is unpredictable, but so is recovery.",
        "You are doing better than you think, even if it doesn’t feel that way.",
        "Strength is found in the moments you keep pushing forward.",
        "You are not alone in this battle, no matter how isolated you feel.",
        "Give yourself the same patience and love that you would offer to someone else.",
        "You are worthy of care, of love, and of brighter days ahead."
    ],
    "NEGATIVE_LOW": [
        "I hear you, and I hope you find something to bring you peace today.",
        "It’s okay if things feel off today. Tomorrow might bring something better.",
        "A rough day doesn’t mean a rough life. Keep going.",
        "Try to be gentle with yourself today.",
        "Every day won’t be perfect, but you are still making progress.",
        "You don’t have to have it all figured out right now.",
        "Even small acts of self-care can help. Maybe take a walk or listen to your favorite song.",
        "I know it’s tough, but you are stronger than you realize.",
        "It’s okay if today isn’t your best. Give yourself permission to rest.",
        "You deserve kindness, even on the hard days.",
        "A setback doesn’t erase all the progress you’ve made.",
        "You have gotten through hard times before, and you will again.",
        "Your feelings are valid, no matter what they are.",
        "It’s okay to take things one step at a time.",
        "Even the smallest victory is still worth celebrating.",
        "Take a moment to breathe and remind yourself that you are enough.",
        "Your worth isn’t defined by how you feel today.",
        "Life is full of ups and downs. Keep holding on.",
        "Don’t underestimate your own strength.",
        "You deserve to take a break and focus on yourself.",
        "Even the heaviest rain eventually stops.",
        "Your struggles are real, but they are not the end of your story.",
        "You don’t have to do everything at once. Small steps matter.",
        "You are capable of finding joy, even on difficult days.",
        "There is still good in the world, even when it’s hard to see.",
        "The way you feel right now doesn’t define your future.",
        "Let yourself rest without guilt.",
        "It’s okay if today is tough. Be patient with yourself.",
        "You are more than your struggles.",
        "Hard days don’t erase all the good ones.",
        "You are not alone in this.",
        "You are enough, just as you are.",
        "Take a deep breath. You’ve got this.",
        "Your emotions are real, and they matter.",
        "Healing isn’t always visible, but that doesn’t mean it’s not happening.",
        "Keep looking for the little things that bring you peace.",
        "Let yourself hope, even in small ways.",
        "You deserve happiness, no matter what.",
        "It’s okay to ask for help when you need it.",
        "You are not your worst day.",
        "Things won’t always be like this.",
        "Every challenge makes you stronger.",
        "Be patient with your own healing.",
        "You are doing better than you think.",
        "Give yourself grace.",
        "You are loved, even if you don’t feel it right now.",
        "You are capable of finding light again.",
        "The best is yet to come."
    ]
}

@app.post("/analyze")
async def chat_response(request: MessageRequest):
    sentiment_result = sentiment_pipeline(request.message)[0]
    label = sentiment_result['label'].upper()
    score = sentiment_result['score']
    category = f"{label}_{'HIGH' if score > 0.9 else 'LOW'}"
    sentiment_response = random.choice(response_dict.get(category, ["I'm here for you."]))
    return {
        "sentiment": label,
        "confidence": score,
        "sentiment_response": sentiment_response
    }

@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    text = whisper_model.transcribe(temp_path)["text"]
    os.unlink(temp_path)
    return {"transcribed_text": text}

@app.post("/text-to-speech")
async def text_to_speech(request: MessageRequest):
    tts = gTTS(request.message, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        audio_path = temp_file.name
    tts.save(audio_path)
    return FileResponse(audio_path, media_type="audio/mpeg", filename="response.mp3")

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

        # Convert NumPy float32 to Python float for JSON serialization
        emotion_scores = {k: float(v) for k, v in analysis.get("emotion", {}).items()}
        dominant_emotion = analysis.get("dominant_emotion", "unknown")

        return {
            "dominant_emotion": dominant_emotion,
            "emotion_scores": emotion_scores
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))