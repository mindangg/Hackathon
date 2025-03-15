from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import whisper
import speech_recognition as sr
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from io import BytesIO
from pydub import AudioSegment
from gtts import gTTS
from fastapi.responses import FileResponse
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load whisper model
try:
    whisper_model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Error loading whisper model: {e}")
    whisper_model = None

# Use a simpler model that doesn't require authentication and has lower hardware requirements
# Options: "facebook/opt-350m", "gpt2", "EleutherAI/gpt-neo-125M", "bigscience/bloom-560m"
MODEL_NAME = "facebook/opt-350m"  # This is much smaller than Llama-2-7b

# Initialize model variables
tokenizer = None
model = None
text_generation_pipeline = None

# Try to load the model
try:
    logger.info(f"Loading simpler model: {MODEL_NAME}")
    
    # You can use a pipeline for simpler models
    text_generation_pipeline = pipeline(
        "text-generation", 
        model=MODEL_NAME,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    logger.info(f"Model {MODEL_NAME} loaded successfully")
except Exception as e:
    logger.error(f"Error loading model {MODEL_NAME}: {e}")
    # Try to fall back to even simpler model
    try:
        logger.info("Trying fallback to GPT-2 model")
        MODEL_NAME = "gpt2"
        text_generation_pipeline = pipeline(
            "text-generation", 
            model=MODEL_NAME,
            device_map="auto" if torch.cuda.is_available() else "cpu"
        )
        logger.info("GPT-2 model loaded successfully")
    except Exception as e2:
        logger.error(f"Error loading fallback model: {e2}")

class MessageRequest(BaseModel):
    message: str

@app.post("/analyze")
async def interpret_sentiment(request: MessageRequest):
    if text_generation_pipeline is None:
        raise HTTPException(status_code=503, detail="Language model not available")
    
    text = request.message
    logger.info(f"Received message: {text[:50]}...")
    
    try:
        # Generate response with the simpler model
        response = text_generation_pipeline(
            text,
            max_length=100,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            num_return_sequences=1
        )
        
        # Extract generated text
        generated_text = response[0]['generated_text']
        
        # Remove the input prompt from the response
        response_text = generated_text[len(text):].strip()
        
        # If the response is empty, return a default message
        if not response_text:
            response_text = "I'm sorry, I couldn't generate a proper response. Please try again."
        
        logger.info(f"Generated response: {response_text[:50]}...")
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not available")
    
    try:
        # Read audio file
        content = await file.read()
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Convert to compatible format if needed
        audio = AudioSegment.from_file(temp_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Save as wav
        wav_path = f"{temp_path}.wav"
        audio.export(wav_path, format="wav")
        
        # Transcribe
        result = whisper_model.transcribe(wav_path)
        text = result["text"]
        
        # Clean up temporary files
        os.unlink(temp_path)
        os.unlink(wav_path)
        
        return {"transcribed_text": text}
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.post("/text-to-speech")
async def text_to_speech(request: MessageRequest):
    try:
        text = request.message
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            audio_path = temp_file.name
        
        # Generate speech
        tts = gTTS(text, lang="en")
        tts.save(audio_path)
        
        # Return the audio file with cleanup
        return FileResponse(
            audio_path, 
            media_type="audio/mpeg", 
            filename="response.mp3",
            background=BackgroundTask(lambda: os.unlink(audio_path))
        )
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.post("/analyze-emotion")
async def analyze_emotion(file: UploadFile = File(...)):
    try:
        # Read the image file
        image_data = await file.read()
        np_image = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Convert BGR to RGB for DeepFace
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Try multiple backends if one fails
        backends = ["opencv", "ssd", "retinaface", "mtcnn", "mediapipe"]
        
        for backend in backends:
            try:
                analysis = DeepFace.analyze(
                    image, 
                    actions=['emotion'], 
                    enforce_detection=False, 
                    detector_backend=backend
                )
                
                # Check if analysis was successful
                if isinstance(analysis, list) and len(analysis) > 0:
                    emotion_data = analysis[0]['emotion']
                    dominant_emotion = analysis[0]['dominant_emotion']
                    
                    # Return both the dominant emotion and the full emotion scores
                    return {
                        "dominant_emotion": dominant_emotion,
                        "emotion_scores": emotion_data,
                        "backend_used": backend
                    }
                
            except Exception as backend_error:
                logger.warning(f"Backend {backend} failed: {str(backend_error)}")
                continue
        
        # If all backends failed
        raise HTTPException(status_code=422, detail="No face could be detected in the image")
        
    except Exception as e:
        logger.error(f"Error analyzing emotion: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing emotion: {str(e)}")

# Add a health check endpoint
@app.get("/health")
async def health_check():
    status = {
        "language_model": text_generation_pipeline is not None,
        "model_name": MODEL_NAME if text_generation_pipeline is not None else "None",
        "whisper_model": whisper_model is not None,
    }
    return status

# Import here to avoid circular imports
# from fastapi.background import BackgroundTask

# Run the server (if not using uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)

