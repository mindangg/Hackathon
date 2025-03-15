# simple_chatbot.py - A minimal FastAPI app using only GPT-2

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer
model = None
tokenizer = None

# Load GPT-2 model directly (avoid using pipeline)
try:
    logger.info("Loading GPT-2 model and tokenizer...")
    
    # Load tokenizer first
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    logger.info("GPT-2 tokenizer loaded successfully")
    
    # Load model second
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    if torch.cuda.is_available():
        model = model.to("cuda")
        logger.info("Model moved to GPU")
    else:
        logger.info("Running on CPU")
        
    logger.info("GPT-2 model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load GPT-2 model: {type(e).__name__}: {str(e)}")

# Request model
class MessageRequest(BaseModel):
    message: str

@app.post("/analyze")
async def analyze_text(request: MessageRequest):
    # Check if model is loaded
    if model is None or tokenizer is None:
        logger.error("Model or tokenizer not available")
        raise HTTPException(
            status_code=503, 
            detail="Language model not available"
        )
    
    message = request.message
    logger.info(f"Received message: {message[:30]}...")
    
    try:
        # Tokenize input
        inputs = tokenizer.encode(message, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
            
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode response
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove input from response
        response_only = response_text[len(message):].strip()
        
        # Handle empty response
        if not response_only:
            response_only = "I'm not sure how to respond to that."
            
        logger.info(f"Generated response: {response_only[:30]}...")
        return {"response": response_only}
    
    except Exception as e:
        logger.error(f"Error generating response: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {
        "model": "gpt2",
        "model_loaded": model is not None and tokenizer is not None,
        "device": "cuda" if torch.cuda.is_available() and model is not None else "cpu"
    }

# Run the server
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run("simple_chatbot:app", host="0.0.0.0", port=5000, reload=False)