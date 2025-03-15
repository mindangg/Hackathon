from transformers import pipeline
import random
import whisper
import speech_recognition as sr
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from io import BytesIO
from pydub import AudioSegment
from gtts import gTTS
from fastapi.responses import FileResponse
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
whisper_model = whisper.load_model("base")

# Response categories
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
        "The universe is cheering for you!", "You're glowing with positivity!", "Keep being you!", "You're unstoppable!", "Go get it, champion!"
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
        "You make the world better!", "Your vibe attracts good things!", "You're a source of joy!", "The world needs your light!"
    ],

    "NEGATIVE_HIGH": [
        "You seem to feel really bad, try to relax.", "It sounds like you’re having a rough time. Take it easy.", 
        "Sorry you're feeling this way. I’m here for you.", "Try to take a deep breath and focus on yourself.", 
        "Remember, tough times don’t last forever.", "You’re stronger than you think. Hang in there.", 
        "It’s okay to feel this way. Be kind to yourself.", "Take a break, clear your mind, and come back stronger.", 
        "You matter, and your feelings are valid.", "I’m here if you need to talk. You’re not alone.", 
        "You're not alone in this struggle.", "It’s okay to not be okay.", "One step at a time, you'll get through this.", 
        "Even the darkest nights end with a sunrise.", "You’re capable of overcoming this.", 
        "No storm lasts forever.", "Your feelings are real and important.", "You deserve love and care.", 
        "Don’t be too hard on yourself.", "I'm here for you.", "Take a moment to breathe.", "You are not defined by this moment.", 
        "Every challenge makes you stronger.", "You are loved and valued.", "I believe in you.", "You have the strength to heal.", 
        "You are not a burden.", "Better days are ahead.", "You are resilient.", "Pain is temporary, but your strength is permanent.", 
        "Take it one breath at a time.", "You are more than your struggles.", "Your story isn’t over yet.", 
        "You have overcome tough times before.", "You deserve kindness, even from yourself.", "Healing takes time, and that’s okay.", 
        "You are not your past mistakes.", "A little progress is still progress.", "This feeling will pass.", "You are brave.", 
        "Be gentle with yourself.", "Your emotions are valid.", "It’s okay to ask for help.", "It’s okay to take things slow.", 
        "Small steps forward still count.", "You are never truly alone.", "Your journey is important.", 
        "Hope is still alive in you.", "You are seen and heard.", "There’s light ahead."
    ],

    "NEGATIVE_LOW": [
        "Aww, that sucks. I wish you a better day.", "That sounds tough, but you'll get through it.", 
        "I’m sorry to hear that. I hope things get better.", "Try to stay strong. You got this.", "It’s okay to feel this way sometimes.", 
        "Sending you good vibes, hope you feel better soon.", "I hope tomorrow brings you something better.", 
        "Small steps forward can make a big difference.", "Stay hopeful, things will improve.", "You're doing your best, and that's enough.", 
        "Hang in there!", "I'm sending you a virtual hug!", "Things can change, don’t lose hope.", "Remember to be kind to yourself.", 
        "You are more than today’s struggle.", "Tomorrow is a new day.", "There is hope, even in the hardest times.", 
        "Healing takes time.", "Focus on what you can control.", "One step at a time.", "Try to take it easy.", 
        "You deserve self-care.", "It’s okay to feel lost sometimes.", "You are worthy of happiness.", "Take a deep breath.", 
        "You are important.", "This is just a chapter, not the whole story.", "Better days are coming.", "Life has ups and downs.", 
        "You have inner strength.", "Things won’t always feel this way.", "You can do this.", "Progress, not perfection.", 
        "Take care of yourself.", "You're not alone in this.", "Even small wins count.", "Give yourself grace.", 
        "Your feelings are valid.", "Healing is not linear.", "Let yourself rest.", "You’re doing the best you can.", 
        "Be patient with yourself.", "You're not broken.", "You are enough.", "Your struggles do not define you."
    ]
}

class MessageRequest(BaseModel):
    message: str

@app.post("/analyze")
def interpret_sentiment(request: MessageRequest):
    text = request.message
    result = classifier(text)[0]
    label = result['label']
    score = result['score']
    
    category = f"{label}_{'HIGH' if score > 0.9 else 'LOW'}"
    response_text = random.choice(response_dict.get(category, ["I'm here for you."]))
    
    return {"response": response_text}

@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    audio_format = file.filename.split(".")[-1]
    audio = AudioSegment.from_file(BytesIO(await file.read()), format=audio_format)
    audio = audio.set_channels(1).set_frame_rate(16000)
    wav_file = BytesIO()
    audio.export(wav_file, format="wav")
    
    text = whisper_model.transcribe(wav_file.getvalue())["text"]
    
    return {"transcribed_text": text}

@app.post("/text-to-speech")
async def text_to_speech(request: MessageRequest):
    text = request.message
    tts = gTTS(text, lang="en")
    audio_path = "response.mp3"
    tts.save(audio_path)
    return FileResponse(audio_path, media_type="audio/mpeg", filename="response.mp3")

@app.post("/analyze-emotion")
@app.post("/analyze-emotion")
async def analyze_emotion(file: UploadFile = File(...)):
    try:
        # Read the image file
        image_data = await file.read()
        np_image = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

        # Convert BGR to RGB for DeepFace
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Analyze facial emotion
        analysis = DeepFace.analyze(
            image, actions=['emotion'], enforce_detection=False, detector_backend="mtcnn"
        )

        # Extract the dominant emotion
        if isinstance(analysis, list) and len(analysis) > 0:
            dominant_emotion = analysis[0]['dominant_emotion']
            return {"emotion": dominant_emotion}
        else:
            return {"error": "No face detected"}

    except Exception as e:
        return {"error": str(e)}
    

# # Test
# text_input = input("How are you feeling: ")
# print(interpret_sentiment(text_input))

# Run the server (if not using uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
